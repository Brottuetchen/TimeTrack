"""
TimeTrack Windows Agent - PyQt6 GUI Version
Modernisierte Version mit vollwertiger GUI statt CLI-Tray
"""
import json
import logging
import os
import signal
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import psutil
import requests
import win32gui
import win32process
from PyQt6.QtWidgets import QApplication

# Bestehende Komponenten
from call_sync import CallSyncManager

# PyQt6 GUI Komponenten
from gui import (
    TrayController,
    MainWindow,
    QuickAssignDialog,
    SettingsDialog,
)

CONFIG_PATH = Path(__file__).with_name("config.json")


def expand_path(value: str) -> str:
    if not value:
        return value
    expanded = os.path.expandvars(value)
    return os.path.expanduser(expanded)


def isoformat(dt: datetime) -> str:
    return dt.isoformat()


def build_logger(log_file: str, debug: bool = False) -> logging.Logger:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("timetrack_agent")


@dataclass
class Config:
    base_url: str
    machine_id: str
    user_id: str
    poll_interval_ms: int
    send_batch_seconds: int
    include_processes: List[str]
    exclude_processes: List[str]
    include_title_keywords: List[str]
    exclude_title_keywords: List[str]
    buffer_file: str
    log_file: str
    verify_ssl: bool
    api_key: Optional[str] = None
    debug_mode: bool = False
    settings_poll_seconds: int = 60
    # Call Sync Settings
    call_sync_enabled: bool = False
    call_sync_interval_minutes: int = 15
    teams_enabled: bool = False
    teams_tenant_id: Optional[str] = None
    teams_client_id: Optional[str] = None
    teams_client_secret: Optional[str] = None
    placetel_enabled: bool = False
    placetel_api_key: Optional[str] = None
    placetel_api_url: Optional[str] = None

    def __post_init__(self):
        self.include_processes = [p.lower() for p in self.include_processes]
        self.exclude_processes = [p.lower() for p in self.exclude_processes]
        self.include_title_keywords = [k.lower() for k in self.include_title_keywords]
        self.exclude_title_keywords = [k.lower() for k in self.exclude_title_keywords]

    @classmethod
    def load(cls) -> "Config":
        if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"config.json fehlt unter {CONFIG_PATH}")
        raw = json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8"))
        raw["buffer_file"] = expand_path(raw.get("buffer_file", "buffer.json"))
        raw["log_file"] = expand_path(raw.get("log_file", "timetrack_agent.log"))
        raw.setdefault("poll_interval_ms", 1500)
        raw.setdefault("send_batch_seconds", 30)
        raw.setdefault("include_processes", [])
        raw.setdefault("exclude_processes", [])
        raw.setdefault("include_title_keywords", [])
        raw.setdefault("exclude_title_keywords", [])
        raw.setdefault("verify_ssl", False)
        raw.setdefault("settings_poll_seconds", 60)
        # Call Sync defaults
        raw.setdefault("call_sync_enabled", False)
        raw.setdefault("call_sync_interval_minutes", 15)
        raw.setdefault("teams_enabled", False)
        raw.setdefault("teams_tenant_id", None)
        raw.setdefault("teams_client_id", None)
        raw.setdefault("teams_client_secret", None)
        raw.setdefault("placetel_enabled", False)
        raw.setdefault("placetel_api_key", None)
        raw.setdefault("placetel_api_url", "https://api.placetel.de/v2")
        return cls(**raw)


class RemoteSettingsManager(threading.Thread):
    def __init__(self, cfg: Config, logger: logging.Logger):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.logger = logger
        self.session = requests.Session()
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._state: Dict[str, Optional[str] | List[str]] = {
            "privacy_mode_until": None,
            "whitelist": [],
            "blacklist": [],
        }

    def run(self):
        while not self._stop_event.is_set():
            self._fetch()
            self._stop_event.wait(max(15, self.cfg.settings_poll_seconds))

    def stop(self):
        self._stop_event.set()

    def _fetch(self):
        try:
            resp = self.session.get(f"{self.cfg.base_url}/settings/logging", timeout=10, verify=self.cfg.verify_ssl)
            resp.raise_for_status()
            data = resp.json()
            with self._lock:
                self._state["privacy_mode_until"] = data.get("privacy_mode_until")
                self._state["whitelist"] = [entry.lower() for entry in data.get("whitelist", [])]
                self._state["blacklist"] = [entry.lower() for entry in data.get("blacklist", [])]
        except requests.RequestException as exc:
            self.logger.debug("Remote settings fetch failed: %s", exc)

    def logging_allowed(self) -> bool:
        with self._lock:
            until = self._state.get("privacy_mode_until")
        if not until:
            return True
        if isinstance(until, str) and until.lower() == "indefinite":
            return False
        try:
            ts = datetime.fromisoformat(until)
        except ValueError:
            return True
        return datetime.now(timezone.utc) >= ts

    def whitelist(self) -> List[str]:
        with self._lock:
            return list(self._state.get("whitelist", []))

    def blacklist(self) -> List[str]:
        with self._lock:
            return list(self._state.get("blacklist", []))

    def privacy_label(self) -> str:
        with self._lock:
            until = self._state.get("privacy_mode_until")
        if not until:
            return "aktiv"
        if isinstance(until, str) and until.lower() == "indefinite":
            return "pausiert (unbegrenzt)"
        try:
            ts = datetime.fromisoformat(until)
        except ValueError:
            return "pausiert (unbekannt)"
        if datetime.now(timezone.utc) < ts:
            return f"pausiert bis {ts.astimezone().strftime('%H:%M')}"
        return "aktiv"


class EventBuffer:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def load(self) -> List[Dict]:
        with self._lock:
            return self._read()

    def append(self, event: Dict):
        with self._lock:
            events = self._read()
            events.append(event)
            self._write(events)

    def replace(self, events: List[Dict]):
        with self._lock:
            self._write(events)

    def _read(self) -> List[Dict]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _write(self, events: List[Dict]):
        self.path.write_text(json.dumps(events, indent=2), encoding="utf-8")

    def count(self) -> int:
        with self._lock:
            return len(self._read())


class WindowTracker(threading.Thread):
    def __init__(self, cfg: Config, buffer: EventBuffer, settings_manager: RemoteSettingsManager, logger: logging.Logger):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.buffer = buffer
        self.settings_manager = settings_manager
        self.logger = logger
        self.poll_interval = max(0.2, cfg.poll_interval_ms / 1000)
        self._stop_event = threading.Event()
        self.current_session: Optional[Dict] = None

    def stop(self):
        self._stop_event.set()

    def run(self):
        self.logger.info("WindowTracker gestartet (%.2fs Poll)", self.poll_interval)
        while not self._stop_event.is_set():
            try:
                info = self._active_window()
                self._handle_window(info)
            except Exception as exc:
                self.logger.exception("Fehler bei Polling: %s", exc)
            self._stop_event.wait(self.poll_interval)
        self._flush_current(final_flush=True)

    def _handle_window(self, info: Optional[Dict]):
        now = datetime.now()
        if not self.settings_manager.logging_allowed():
            self.logger.debug("Privacy-Modus aktiv, Tracking pausiert")
            if self.current_session:
                self._flush_current()
            return
        if not info:
            self.logger.debug("Kein aktives Fenster erkannt")
            if self.current_session:
                self._flush_current()
            return
        if not self._should_track(info):
            self.logger.debug("Fenster wird nicht getrackt: %s - %s", info["process"], info["title"][:50])
            if self.current_session:
                self._flush_current()
            return
        if not self.current_session:
            self.logger.debug("Neue Session gestartet: %s", info["process"])
            self.current_session = {
                "timestamp_start": now,
                "window_title": info["title"],
                "process_name": info["process"],
            }
            return
        if info["process"] != self.current_session["process_name"] or info["title"] != self.current_session["window_title"]:
            self._flush_current()
            self.logger.debug("Session-Wechsel: %s", info["process"])
            self.current_session = {
                "timestamp_start": now,
                "window_title": info["title"],
                "process_name": info["process"],
            }

    def _flush_current(self, final_flush: bool = False):
        if not self.current_session:
            return
        end_ts = datetime.now()
        start_ts = self.current_session["timestamp_start"]
        duration = (end_ts - start_ts).total_seconds()
        if duration < 2:
            self.logger.debug("Kurz-Event verworfen (%ss)", duration)
        else:
            event = {
                "timestamp_start": isoformat(start_ts),
                "timestamp_end": isoformat(end_ts),
                "duration_seconds": int(duration),
                "window_title": self.current_session["window_title"],
                "process_name": self.current_session["process_name"],
                "machine_id": self.cfg.machine_id,
                "user_id": self.cfg.user_id,
            }
            self.buffer.append(event)
            self.logger.info("Event gespeichert: %s", event["process_name"])
        self.current_session = None
        if final_flush:
            self.logger.info("Tracker gestoppt, offene Session geschlossen")

    def _active_window(self) -> Optional[Dict]:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            name = proc.name().lower()
        except (psutil.Error, OSError):
            return None
        title = win32gui.GetWindowText(hwnd).strip()
        if not title:
            return None
        return {"process": name, "title": title}

    def _should_track(self, info: Dict) -> bool:
        proc = info["process"]
        title = info["title"].lower()
        remote_whitelist = self.settings_manager.whitelist()
        remote_blacklist = self.settings_manager.blacklist()

        if remote_whitelist and proc not in remote_whitelist:
            self.logger.debug("⊗ %s: nicht in Remote-Whitelist", proc)
            return False
        if proc in remote_blacklist:
            self.logger.debug("⊗ %s: in Remote-Blacklist", proc)
            return False
        if self.cfg.include_processes and proc not in self.cfg.include_processes:
            self.logger.debug("⊗ %s: nicht in include_processes %s", proc, self.cfg.include_processes)
            return False
        if proc in self.cfg.exclude_processes:
            self.logger.debug("⊗ %s: in exclude_processes", proc)
            return False
        if self.cfg.include_title_keywords and not any(keyword in title for keyword in self.cfg.include_title_keywords):
            self.logger.debug("⊗ %s: Titel enthält keine include_title_keywords", proc)
            return False
        if any(keyword in title for keyword in self.cfg.exclude_title_keywords):
            self.logger.debug("⊗ %s: Titel enthält exclude_title_keyword", proc)
            return False

        self.logger.debug("✓ %s wird getrackt", proc)
        return True


class EventSender(threading.Thread):
    def __init__(self, cfg: Config, buffer: EventBuffer, logger: logging.Logger):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.buffer = buffer
        self.logger = logger
        self._stop_event = threading.Event()
        self.session = requests.Session()
        self.last_success: Optional[datetime] = None
        self.last_error: Optional[str] = None

    def stop(self):
        self._stop_event.set()

    def run(self):
        self.logger.info("EventSender gestartet (Batch %ss)", self.cfg.send_batch_seconds)
        while not self._stop_event.is_set():
            try:
                self._send_batch()
            except Exception as exc:
                self.logger.warning("Senden fehlgeschlagen: %s", exc)
            self._stop_event.wait(self.cfg.send_batch_seconds)

    def _send_batch(self):
        events = self.buffer.load()
        if not events:
            return
        remaining = []
        sent_any = False
        for event in events:
            if self._post_event(event):
                self.logger.info("Event übertragen (%s)", event["process_name"])
                sent_any = True
            else:
                remaining.append(event)
        self.buffer.replace(remaining)
        if sent_any:
            self.last_success = datetime.now()
            self.last_error = None

    def _post_event(self, event: Dict) -> bool:
        headers = {"Content-Type": "application/json"}
        if self.cfg.api_key:
            headers["Authorization"] = f"Bearer {self.cfg.api_key}"
        attempts = 3
        last_error = ""
        for attempt in range(1, attempts + 1):
            try:
                resp = self.session.post(
                    f"{self.cfg.base_url}/events/window",
                    json=event,
                    timeout=10,
                    headers=headers,
                    verify=self.cfg.verify_ssl,
                )
                if resp.status_code < 300:
                    return True
                last_error = f"HTTP {resp.status_code}: {resp.text}"
                raise requests.RequestException(last_error)
            except requests.RequestException as exc:
                last_error = str(exc)
                self.logger.warning("POST Versuch %s/%s fehlgeschlagen: %s", attempt, attempts, last_error)
                import time
                time.sleep(2)
        self.last_error = last_error or "Unbekannter Fehler"
        return False


class QtApp:
    """PyQt6 Application Wrapper."""

    def __init__(self, cfg: Config, logger: logging.Logger):
        self.cfg = cfg
        self.logger = logger

        # QApplication
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Buffer & Threads
        self.buffer = EventBuffer(cfg.buffer_file)
        self.settings_manager = RemoteSettingsManager(cfg, logger)
        self.tracker = WindowTracker(cfg, self.buffer, self.settings_manager, logger)
        self.sender = EventSender(cfg, self.buffer, logger)

        # CallSyncManager
        self.call_sync_manager = None
        if cfg.call_sync_enabled and (cfg.teams_enabled or cfg.placetel_enabled):
            logger.info("Starte CallSyncManager...")
            self.call_sync_manager = CallSyncManager(
                base_url=cfg.base_url,
                user_id=cfg.user_id,
                logger=logger,
                sync_interval_minutes=cfg.call_sync_interval_minutes,
                teams_enabled=cfg.teams_enabled,
                teams_tenant_id=cfg.teams_tenant_id,
                teams_client_id=cfg.teams_client_id,
                teams_client_secret=cfg.teams_client_secret,
                placetel_enabled=cfg.placetel_enabled,
                placetel_api_key=cfg.placetel_api_key,
                placetel_api_url=cfg.placetel_api_url,
                verify_ssl=cfg.verify_ssl,
                api_key=cfg.api_key
            )

        # PyQt6 GUI
        self.tray = TrayController(
            app=self.app,
            logger=logger,
            tracking_enabled=True,
            call_sync_enabled=cfg.call_sync_enabled
        )

        self.main_window = None
        self.quick_assign_dialog = None
        self.settings_dialog = None

        # Connect Signals
        self._connect_signals()

        # Start Threads
        self.settings_manager.start()
        self.tracker.start()
        self.sender.start()
        if self.call_sync_manager:
            self.call_sync_manager.start()

        # Status Update Timer
        from PyQt6.QtCore import QTimer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_tray_status)
        self.status_timer.start(5000)  # Alle 5 Sekunden

        logger.info("PyQt6 Application initialisiert")

    def _connect_signals(self):
        """Verbinde Qt Signals."""
        self.tray.dashboard_requested.connect(self._show_dashboard)
        self.tray.quick_assign_requested.connect(self._show_quick_assign)
        self.tray.settings_requested.connect(self._show_settings)
        self.tray.tracking_toggled.connect(self._toggle_tracking)
        self.tray.send_now_requested.connect(self._send_now)
        self.tray.call_sync_requested.connect(self._trigger_call_sync)
        self.tray.quit_requested.connect(self.quit)

    def _show_dashboard(self):
        """Öffnet Dashboard."""
        if not self.main_window:
            self.main_window = MainWindow(
                logger=self.logger,
                base_url=self.cfg.base_url,
                user_id=self.cfg.user_id,
                api_key=self.cfg.api_key,
                verify_ssl=self.cfg.verify_ssl,
                call_sync_enabled=self.cfg.call_sync_enabled
            )
            self.main_window.quick_assign_requested.connect(self._show_quick_assign)
            self.main_window.settings_requested.connect(self._show_settings)

        self.main_window.show()
        self.main_window.activateWindow()

    def _show_quick_assign(self):
        """Öffnet Quick-Assign Dialog."""
        dialog = QuickAssignDialog(
            logger=self.logger,
            base_url=self.cfg.base_url,
            user_id=self.cfg.user_id,
            api_key=self.cfg.api_key,
            verify_ssl=self.cfg.verify_ssl
        )
        dialog.exec()

    def _show_settings(self):
        """Öffnet Settings Dialog."""
        dialog = SettingsDialog(
            logger=self.logger,
            base_url=self.cfg.base_url,
            user_id=self.cfg.user_id,
            api_key=self.cfg.api_key,
            verify_ssl=self.cfg.verify_ssl
        )
        dialog.exec()

    def _toggle_tracking(self, enabled: bool):
        """Toggle Tracking."""
        if enabled and not self.tracker.is_alive():
            self.tracker = WindowTracker(self.cfg, self.buffer, self.settings_manager, self.logger)
            self.tracker.start()
        elif not enabled and self.tracker.is_alive():
            self.tracker.stop()
            self.tracker.join(timeout=2)

    def _send_now(self):
        """Manuelle Event-Übertragung."""
        self.logger.info("Manueller Send-Lauf")
        self.sender._send_batch()
        self._update_tray_status()
        self.tray.show_notification("TimeTrack", "Events wurden gesendet")

    def _trigger_call_sync(self):
        """Trigger Call-Sync."""
        if self.call_sync_manager:
            self.logger.info("Manueller Call-Sync getriggert")
            self.call_sync_manager.trigger_manual_sync()
            self.tray.show_notification("TimeTrack Call-Sync", "Call-Sync wurde gestartet")

    def _update_tray_status(self):
        """Update Tray Status."""
        buffer_count = self.buffer.count()
        last_upload = self.sender.last_success.strftime("%d.%m.%Y %H:%M") if self.sender.last_success else "noch nie"
        last_error = self.sender.last_error or "–"
        privacy_label = self.settings_manager.privacy_label()

        call_sync_status = None
        if self.call_sync_manager:
            call_sync_status = self.call_sync_manager.get_status()

        self.tray.update_status(
            buffer_count=buffer_count,
            last_upload=last_upload,
            last_error=last_error,
            privacy_label=privacy_label,
            call_sync_status=call_sync_status
        )

        # Update Dashboard falls offen
        if self.main_window and self.main_window.isVisible():
            self.main_window.dashboard_widget.update_stats(buffer_count, privacy_label)

    def quit(self):
        """Beendet die Anwendung."""
        self.logger.info("Beende Anwendung...")

        # Stop Threads
        if self.tracker.is_alive():
            self.tracker.stop()
            self.tracker.join(timeout=2)
        if self.sender.is_alive():
            self.sender.stop()
            self.sender.join(timeout=2)
        if self.call_sync_manager and self.call_sync_manager.is_alive():
            self.call_sync_manager.stop()
            self.call_sync_manager.join(timeout=2)

        self.settings_manager.stop()
        self.status_timer.stop()
        self.tray.cleanup()

        self.app.quit()
        self.logger.info("Anwendung beendet")

    def run(self):
        """Startet die Qt Event Loop."""
        return self.app.exec()


def main():
    cfg = Config.load()
    logger = build_logger(cfg.log_file, debug=cfg.debug_mode)

    qt_app = QtApp(cfg, logger)

    # Signal Handler
    def handle_signal(signum, frame):
        logger.info("Signal %s, exit", signum)
        qt_app.quit()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    sys.exit(qt_app.run())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Fataler Fehler: {exc}", file=sys.stderr)
        sys.exit(1)
