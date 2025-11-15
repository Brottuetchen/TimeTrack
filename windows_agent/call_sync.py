"""
CallSyncManager für Windows Agent - Synchronisiert Teams/Placetel Calls
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests


class CallSyncManager(threading.Thread):
    """
    Daemon-Thread der periodisch Teams und/oder Placetel Calls synchronisiert.

    - Läuft alle X Minuten (konfigurierbar)
    - Nutzt das Backend /calls/sync/teams Endpoint
    - Speichert letzten Sync-Zeitpunkt
    - Kann manuell getriggert werden
    """

    def __init__(
        self,
        base_url: str,
        user_id: str,
        logger: logging.Logger,
        sync_interval_minutes: int = 15,
        teams_enabled: bool = False,
        teams_tenant_id: Optional[str] = None,
        teams_client_id: Optional[str] = None,
        teams_client_secret: Optional[str] = None,
        placetel_enabled: bool = False,
        placetel_api_key: Optional[str] = None,
        placetel_api_url: Optional[str] = None,
        verify_ssl: bool = False,
        api_key: Optional[str] = None
    ):
        super().__init__(daemon=True)
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.logger = logger
        self.sync_interval_minutes = sync_interval_minutes

        # Teams Settings
        self.teams_enabled = teams_enabled
        self.teams_tenant_id = teams_tenant_id
        self.teams_client_id = teams_client_id
        self.teams_client_secret = teams_client_secret

        # Placetel Settings (für zukünftige Erweiterung)
        self.placetel_enabled = placetel_enabled
        self.placetel_api_key = placetel_api_key
        self.placetel_api_url = placetel_api_url

        self.verify_ssl = verify_ssl
        self.api_key = api_key

        self._stop_event = threading.Event()
        self._manual_trigger = threading.Event()
        self._lock = threading.Lock()

        # Status tracking
        self.last_sync_time: Optional[datetime] = None
        self.last_sync_success: bool = False
        self.last_sync_error: Optional[str] = None
        self.sync_count: int = 0

        # Session für HTTP requests
        self.session = requests.Session()
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

    def stop(self):
        """Stoppt den Sync-Thread gracefully."""
        self._stop_event.set()

    def trigger_manual_sync(self):
        """Triggert einen manuellen Sync außerhalb des Intervalls."""
        self._manual_trigger.set()
        self.logger.info("Manueller Call-Sync wurde getriggert")

    def get_status(self) -> Dict[str, Any]:
        """Gibt den aktuellen Status zurück."""
        with self._lock:
            return {
                "enabled": self.teams_enabled or self.placetel_enabled,
                "teams_enabled": self.teams_enabled,
                "placetel_enabled": self.placetel_enabled,
                "interval_minutes": self.sync_interval_minutes,
                "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
                "last_sync_success": self.last_sync_success,
                "last_sync_error": self.last_sync_error,
                "sync_count": self.sync_count,
                "next_sync_in_seconds": self._get_next_sync_seconds()
            }

    def _get_next_sync_seconds(self) -> Optional[int]:
        """Berechnet Sekunden bis zum nächsten Sync."""
        if not self.last_sync_time:
            return 0
        next_sync = self.last_sync_time + timedelta(minutes=self.sync_interval_minutes)
        delta = (next_sync - datetime.now()).total_seconds()
        return max(0, int(delta))

    def _update_backend_settings(self):
        """
        Schreibt die aktuellen Teams-Credentials ins Backend.
        Nutzt das Settings-API um Teams-Credentials zu speichern.
        """
        if not self.teams_enabled:
            return

        try:
            url = f"{self.base_url}/settings/logging"

            # Erst Settings laden
            resp = self.session.get(url, verify=self.verify_ssl, timeout=10)
            if resp.status_code != 200:
                self.logger.warning(f"Konnte Settings nicht laden: {resp.status_code}")
                return

            current_settings = resp.json()

            # Teams-Credentials updaten
            current_settings.update({
                "teams_tenant_id": self.teams_tenant_id,
                "teams_client_id": self.teams_client_id,
                "teams_client_secret": self.teams_client_secret
            })

            # Settings zurückschreiben
            resp = self.session.post(url, json=current_settings, verify=self.verify_ssl, timeout=10)
            if resp.status_code == 200:
                self.logger.info("Teams-Credentials erfolgreich ins Backend geschrieben")
            else:
                self.logger.warning(f"Konnte Teams-Credentials nicht schreiben: {resp.status_code}")

        except Exception as e:
            self.logger.error(f"Fehler beim Updaten der Backend-Settings: {e}")

    def _sync_teams_calls(self):
        """
        Synchronisiert Teams Calls für die letzte Periode.
        Nutzt das Backend /calls/sync/teams Endpoint.
        """
        if not self.teams_enabled:
            return

        # Zeitfenster: letzter Sync bis jetzt (oder letzte 24h falls erster Sync)
        end = datetime.now()
        if self.last_sync_time:
            start = self.last_sync_time
        else:
            start = end - timedelta(hours=24)

        try:
            url = f"{self.base_url}/calls/sync/teams"
            params = {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "user_id": self.user_id
            }

            self.logger.info(f"Starte Teams-Sync: {start.isoformat()} bis {end.isoformat()}")

            resp = self.session.post(url, params=params, verify=self.verify_ssl, timeout=60)

            if resp.status_code == 200:
                result = resp.json()
                self.logger.info(f"Teams-Sync erfolgreich: {result}")
                with self._lock:
                    self.last_sync_success = True
                    self.last_sync_error = None
            elif resp.status_code == 501:
                # Not Implemented - Teams Integration noch nicht fertig
                error_msg = "Teams-Integration noch nicht vollständig implementiert (msal/httpx fehlt)"
                self.logger.warning(error_msg)
                with self._lock:
                    self.last_sync_success = False
                    self.last_sync_error = error_msg
            else:
                error_msg = f"Teams-Sync fehlgeschlagen: HTTP {resp.status_code} - {resp.text}"
                self.logger.error(error_msg)
                with self._lock:
                    self.last_sync_success = False
                    self.last_sync_error = error_msg

        except requests.exceptions.RequestException as e:
            error_msg = f"Netzwerkfehler bei Teams-Sync: {e}"
            self.logger.error(error_msg)
            with self._lock:
                self.last_sync_success = False
                self.last_sync_error = error_msg
        except Exception as e:
            error_msg = f"Unerwarteter Fehler bei Teams-Sync: {e}"
            self.logger.exception(error_msg)
            with self._lock:
                self.last_sync_success = False
                self.last_sync_error = error_msg

    def _sync_placetel_calls(self):
        """
        Placeholder für zukünftige Placetel-Synchronisation.

        Placetel nutzt primär Webhooks, könnte aber auch ein Pull-API haben.
        TODO: Implementieren falls Placetel ein Call-History-API hat.
        """
        if not self.placetel_enabled:
            return

        self.logger.info("Placetel-Sync: Noch nicht implementiert (Webhook-basiert)")

    def run(self):
        """Haupt-Loop des Sync-Threads."""
        self.logger.info(
            f"CallSyncManager gestartet (Intervall: {self.sync_interval_minutes} min, "
            f"Teams: {self.teams_enabled}, Placetel: {self.placetel_enabled})"
        )

        # Beim Start: Teams-Credentials ins Backend schreiben (falls aktiviert)
        if self.teams_enabled:
            self._update_backend_settings()

        # Initial Sync nach 10 Sekunden
        time.sleep(10)

        while not self._stop_event.is_set():
            try:
                # Sync durchführen
                self.logger.info("Starte Call-Synchronisation...")

                if self.teams_enabled:
                    self._sync_teams_calls()

                if self.placetel_enabled:
                    self._sync_placetel_calls()

                with self._lock:
                    self.last_sync_time = datetime.now()
                    self.sync_count += 1

                self.logger.info(f"Call-Sync abgeschlossen (#{self.sync_count})")

            except Exception as e:
                self.logger.exception(f"Kritischer Fehler im Call-Sync: {e}")

            # Warten bis zum nächsten Intervall oder manueller Trigger
            interval_seconds = self.sync_interval_minutes * 60
            wait_start = time.time()

            while time.time() - wait_start < interval_seconds:
                # Check ob manueller Trigger oder Stop
                if self._manual_trigger.wait(timeout=1.0):
                    self._manual_trigger.clear()
                    self.logger.info("Manueller Sync-Trigger erkannt")
                    break

                if self._stop_event.is_set():
                    break

        self.logger.info("CallSyncManager wurde gestoppt")
