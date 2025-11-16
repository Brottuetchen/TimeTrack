import ctypes
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import psutil
import pystray
import requests
import win32gui
import win32process
from PIL import Image, ImageDraw
from pystray import MenuItem

from call_sync import CallSyncManager

# Config-Editor wird bei Bedarf importiert (optional für Standalone-Betrieb)
try:
    from config_editor import ConfigEditorDialog
    from PyQt6.QtWidgets import QApplication
    CONFIG_EDITOR_AVAILABLE = True
except ImportError:
    CONFIG_EDITOR_AVAILABLE = False

# Config-Pfad: Erst im Script-Verzeichnis suchen, sonst in APPDATA
def get_config_path() -> Path:
    """Ermittelt den Config-Pfad (Script-Verzeichnis oder APPDATA)"""
    # Bei EXE-Build ist __file__ im temp-Verzeichnis, daher APPDATA bevorzugen
    if getattr(sys, 'frozen', False):
        # Läuft als EXE
        appdata = Path(os.path.expandvars('%APPDATA%')) / 'TimeTrack'
        appdata.mkdir(parents=True, exist_ok=True)
        return appdata / 'config.json'
    else:
        # Läuft als Script - erst lokales Verzeichnis prüfen
        local_config = Path(__file__).with_name("config.json")
        if local_config.exists():
            return local_config
        # Sonst APPDATA verwenden
        appdata = Path(os.path.expandvars('%APPDATA%')) / 'TimeTrack'
        appdata.mkdir(parents=True, exist_ok=True)
        return appdata / 'config.json'

CONFIG_PATH = get_config_path()


def expand_path(value: str) -> str:
    if not value:
        return value
    expanded = os.path.expandvars(value)
    return os.path.expanduser(expanded)


def isoformat(dt: datetime) -> str:
    return dt.isoformat()


def build_logger(log_file: str) -> logging.Logger:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("timetrack_agent")


def open_path(path: Path):
    try:
        if os.name == "nt":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as exc:
        logging.getLogger("timetrack_agent").warning("Konnte %s nicht öffnen: %s", path, exc)


def create_default_config() -> dict:
    """Erstellt eine Default-Konfiguration"""
    import socket
    hostname = socket.gethostname()

    return {
        "base_url": "http://localhost:8000",
        "user_id": "BITTE_EINTRAGEN",
        "machine_id": hostname,
        "poll_interval_ms": 1500,
        "send_batch_seconds": 30,
        "settings_poll_seconds": 60,
        "include_processes": [],
        "exclude_processes": [],
        "include_title_keywords": [],
        "exclude_title_keywords": [],
        "buffer_file": "%APPDATA%\\TimeTrack\\buffer.json",
        "log_file": "%APPDATA%\\TimeTrack\\agent.log",
        "verify_ssl": False,
        "api_key": None,
        "call_sync_enabled": False,
        "call_sync_interval_minutes": 15,
        "teams_enabled": False,
        "teams_tenant_id": None,
        "teams_client_id": None,
        "teams_client_secret": None,
        "placetel_enabled": False,
        "placetel_api_key": None,
        "placetel_api_url": "https://api.placetel.de/v2"
    }


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
            # Erstelle Default-Config
            default_config = create_default_config()
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            print(f"Default-Konfiguration erstellt: {CONFIG_PATH}")
            print("Bitte öffne die Config über das Tray-Menü und passe sie an!")

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
    def __init__(self, cfg: Config, buffer: EventBuffer, settings_manager: "RemoteSettingsManager", logger: logging.Logger):
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
            if self.current_session:
                self._flush_current()
            return
        if not info:
            if self.current_session:
                self._flush_current()
            return
        if not self._should_track(info):
            if self.current_session:
                self._flush_current()
            return
        if not self.current_session:
            self.current_session = {
                "timestamp_start": now,
                "window_title": info["title"],
                "process_name": info["process"],
            }
            return
        if info["process"] != self.current_session["process_name"] or info["title"] != self.current_session["window_title"]:
            self._flush_current()
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
            return False
        if proc in remote_blacklist:
            return False
        if self.cfg.include_processes and proc not in self.cfg.include_processes:
            return False
        if proc in self.cfg.exclude_processes:
            return False
        if self.cfg.include_title_keywords and not any(keyword in title for keyword in self.cfg.include_title_keywords):
            return False
        if any(keyword in title for keyword in self.cfg.exclude_title_keywords):
            return False
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
                time.sleep(2)
        self.last_error = last_error or "Unbekannter Fehler"
        return False


class StatusThread(threading.Thread):
    def __init__(self, controller: "TrayController", interval: float = 15.0):
        super().__init__(daemon=True)
        self.controller = controller
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.wait(self.interval):
            self.controller.update_tooltip()

    def stop(self):
        self._stop_event.set()


class TrayController:
    def __init__(
        self,
        tracker: WindowTracker,
        sender: EventSender,
        buffer: EventBuffer,
        cfg: Config,
        settings_manager: RemoteSettingsManager,
        logger: logging.Logger,
        call_sync_manager: Optional[CallSyncManager] = None,
    ):
        self.tracker = tracker
        self.sender = sender
        self.buffer = buffer
        self.cfg = cfg
        self.settings_manager = settings_manager
        self.call_sync_manager = call_sync_manager
        self.logger = logger
        self.tracking_enabled = True
        self.menu_toggle = MenuItem("Tracking aktiv", self.toggle_tracking, checked=lambda item: self.tracking_enabled)

        # Menü-Einträge dynamisch zusammenstellen
        menu_items = [
            self.menu_toggle,
            MenuItem("Offene Events senden", self.send_now),
            MenuItem("Status anzeigen", self.show_status),
        ]

        # Call-Sync Menü-Eintrag nur wenn aktiviert
        if call_sync_manager:
            menu_items.append(MenuItem("Call-Sync jetzt ausführen", self.trigger_call_sync))

        # Config-Editor oder öffnen
        if CONFIG_EDITOR_AVAILABLE:
            menu_items.append(MenuItem("Einstellungen bearbeiten", self.edit_config))
        else:
            menu_items.append(MenuItem("Config öffnen", self.open_config))

        menu_items.extend([
            MenuItem("Logdatei öffnen", self.open_log),
            MenuItem("Beenden", self.quit),
        ])

        self.icon = pystray.Icon(
            "timetrack",
            self._icon(active=True),
            "TimeTrack",
            menu=pystray.Menu(*menu_items),
        )
        self.status_thread = StatusThread(self)

    def _icon(self, active: bool) -> Image.Image:
        color = (0, 180, 0) if active else (200, 80, 0)
        image = Image.new("RGB", (64, 64), color)
        draw = ImageDraw.Draw(image)
        draw.ellipse((16, 16, 48, 48), fill=(255, 255, 255))
        return image

    def toggle_tracking(self, icon, item):
        self.tracking_enabled = not self.tracking_enabled
        if self.tracking_enabled and not self.tracker.is_alive():
            self.tracker = restart_thread(self.tracker)
        elif not self.tracking_enabled and self.tracker.is_alive():
            self.tracker.stop()
            self.tracker.join(timeout=2)
        icon.icon = self._icon(self.tracking_enabled)
        self.logger.info("Tracking %s", "aktiv" if self.tracking_enabled else "pausiert")
        self.update_tooltip()

    def send_now(self, *_):
        self.logger.info("Manueller Send-Lauf")
        self.sender._send_batch()
        self.update_tooltip()

    def trigger_call_sync(self, *_):
        """Triggert einen manuellen Call-Sync."""
        if self.call_sync_manager:
            self.logger.info("Manueller Call-Sync getriggert")
            self.call_sync_manager.trigger_manual_sync()
            self._show_message("Call-Sync wurde gestartet", "TimeTrack Call-Sync")
        else:
            self._show_message("Call-Sync ist nicht aktiviert", "TimeTrack Call-Sync")

    def show_status(self, *_):
        self._show_message(self.status_text(), "TimeTrack Status")

    def edit_config(self, *_):
        """Öffnet den Config-Editor Dialog"""
        if not CONFIG_EDITOR_AVAILABLE:
            self.open_config()
            return

        try:
            # PyQt6 Application erstellen falls nötig
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            # Config-Editor Dialog öffnen
            dialog = ConfigEditorDialog(CONFIG_PATH)
            dialog.exec()

            self.logger.info("Config-Editor geschlossen")
        except Exception as exc:
            self.logger.exception("Fehler beim Öffnen des Config-Editors: %s", exc)
            self._show_message(
                f"Config-Editor konnte nicht geöffnet werden:\n{exc}",
                "Fehler"
            )

    def open_config(self, *_):
        open_path(Path(CONFIG_PATH))

    def open_log(self, *_):
        log_path = Path(self.cfg.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if not log_path.exists():
            log_path.touch()
        open_path(log_path)

    def quit(self, icon, item):
        self.logger.info("Tray wird beendet")
        if self.tracker.is_alive():
            self.tracker.stop()
            self.tracker.join(timeout=2)
        if self.sender.is_alive():
            self.sender.stop()
            self.sender.join(timeout=2)
        if self.call_sync_manager and self.call_sync_manager.is_alive():
            self.call_sync_manager.stop()
            self.call_sync_manager.join(timeout=2)
        self.status_thread.stop()
        self.settings_manager.stop()
        icon.stop()

    def run(self):
        if not self.tracker.is_alive():
            self.tracker.start()
        if not self.sender.is_alive():
            self.sender.start()
        self.status_thread.start()
        self.update_tooltip()
        self.icon.run()

    def status_text(self) -> str:
        buffer_size = self.buffer.count()
        last_sent = self.sender.last_success.strftime("%d.%m.%Y %H:%M") if self.sender.last_success else "noch nie"
        last_error = self.sender.last_error or "–"
        tracking = "Tracking aktiv" if self.tracking_enabled else "Tracking pausiert"

        status_lines = [
            f"{tracking}",
            f"Offene Events: {buffer_size}",
            f"Letzter Upload: {last_sent}",
            f"Letzter Fehler: {last_error}",
            f"Privacy-Modus: {self.settings_manager.privacy_label()}"
        ]

        # Call-Sync Status hinzufügen wenn aktiviert
        if self.call_sync_manager:
            sync_status = self.call_sync_manager.get_status()
            last_sync = sync_status.get("last_sync_time")
            if last_sync:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(last_sync)
                    last_sync_str = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    last_sync_str = "unbekannt"
            else:
                last_sync_str = "noch nie"

            next_sync_sec = sync_status.get("next_sync_in_seconds", 0)
            next_sync_min = int(next_sync_sec / 60)

            sync_ok = "✓" if sync_status.get("last_sync_success") else "✗"

            status_lines.extend([
                "",
                f"Call-Sync: {sync_ok} (alle {sync_status['interval_minutes']} min)",
                f"Letzter Sync: {last_sync_str}",
                f"Nächster Sync in: {next_sync_min} min"
            ])

            if sync_status.get("last_sync_error"):
                status_lines.append(f"Fehler: {sync_status['last_sync_error'][:50]}")

        return "\n".join(status_lines)

    def update_tooltip(self):
        status = "aktiv" if self.tracking_enabled else "pausiert"
        self.icon.title = f"TimeTrack – {status}"

    def _show_message(self, text: str, title: str):
        try:
            if os.name == "nt":
                ctypes.windll.user32.MessageBoxW(None, text, title, 0x40)
            elif sys.platform == "darwin":
                subprocess.Popen(["osascript", "-e", f'display notification \"{text}\" with title \"{title}\"'])
            else:
                subprocess.Popen(["notify-send", title, text])
        except Exception as exc:
            self.logger.warning("Konnte Statusmeldung nicht anzeigen: %s", exc)


def restart_thread(thread: WindowTracker) -> WindowTracker:
    cfg = thread.cfg
    buffer = thread.buffer
    logger = thread.logger
    new_thread = WindowTracker(cfg, buffer, logger)
    new_thread.start()
    return new_thread


def main():
    cfg = Config.load()
    logger = build_logger(cfg.log_file)
    buffer = EventBuffer(cfg.buffer_file)

    settings_manager = RemoteSettingsManager(cfg, logger)
    settings_manager.start()

    tracker = WindowTracker(cfg, buffer, settings_manager, logger)
    sender = EventSender(cfg, buffer, logger)

    # CallSyncManager starten wenn aktiviert
    call_sync_manager = None
    if cfg.call_sync_enabled and (cfg.teams_enabled or cfg.placetel_enabled):
        logger.info("Starte CallSyncManager...")
        call_sync_manager = CallSyncManager(
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
        call_sync_manager.start()
    else:
        logger.info("CallSyncManager deaktiviert (call_sync_enabled=%s, teams=%s, placetel=%s)",
                   cfg.call_sync_enabled, cfg.teams_enabled, cfg.placetel_enabled)

    controller = TrayController(tracker, sender, buffer, cfg, settings_manager, logger, call_sync_manager)

    def handle_signal(signum, frame):
        logger.info("Signal %s, exit", signum)
        if call_sync_manager:
            call_sync_manager.stop()
        controller.quit(controller.icon, None)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    controller.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Fataler Fehler: {exc}", file=sys.stderr)
        sys.exit(1)

