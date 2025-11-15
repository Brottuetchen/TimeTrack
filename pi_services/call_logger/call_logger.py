#!/usr/bin/env python3
"""
Call logger daemon for Raspberry Pi.

Listens to oFono (BlueZ/HFP) events via D-Bus, translates them into the FastAPI event schema,
and POSTs them to /events/phone. Designed for headless Pi connected to an iPhone.
"""

import json
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import requests
from gi.repository import GLib
from pydbus import SystemBus

API_BASE_URL = os.getenv("TIMETRACK_API", "http://127.0.0.1:8000")
DEVICE_ID = os.getenv("TIMETRACK_DEVICE_ID", "raspi-pi5")
USER_ID = os.getenv("TIMETRACK_USER_ID", "default")
CONTACTS_FILE = os.getenv("TIMETRACK_CONTACTS", "/opt/timetrack/contacts.json")
LOG_LEVEL = os.getenv("TIMETRACK_LOG_LEVEL", "INFO").upper()


class CallLogger:
    def __init__(self):
        self.session = requests.Session()
        self.bus = SystemBus()
        self.loop = GLib.MainLoop()
        self.active_calls: Dict[str, Dict] = {}
        self.contacts = self._load_contacts(CONTACTS_FILE)
        self.logger = logging.getLogger("call_logger")
        self.logger.setLevel(LOG_LEVEL)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        self.logger.addHandler(handler)

    def _load_contacts(self, path: str) -> Dict[str, str]:
        file_path = Path(path)
        if not file_path.exists():
            return {}
        try:
            return {item["number"]: item.get("name", "") for item in json.loads(file_path.read_text())}
        except Exception as exc:  # pragma: no cover
            self.logger.warning("Could not read contacts file %s: %s", file_path, exc)
            return {}

    def start(self):
        self.logger.info("Starting call logger, base_url=%s", API_BASE_URL)
        manager = self.bus.get("org.ofono", "/")
        for modem_path, props in manager.GetModems():
            self.logger.info("Watching modem %s (%s)", modem_path, props.get("Name"))
            self._watch_modem(modem_path)
        manager.onModemAdded = self._watch_modem  # dynamic plug
        self.loop.run()

    def _watch_modem(self, modem_path, *_):
        voice = self.bus.get("org.ofono", modem_path)
        voice.onCallAdded = self._call_added
        voice.onCallRemoved = self._call_removed
        self.logger.info("Subscribed to VoiceCallManager on %s", modem_path)

    def _call_added(self, call_path, properties):
        call_id = str(call_path)
        now = datetime.now()
        direction = "INCOMING" if properties.get("Incoming") else "OUTGOING"
        number = properties.get("LineIdentification", "")
        contact = self.contacts.get(number, "")
        self.active_calls[call_id] = {
            "start": now,
            "direction": direction,
            "number": number,
            "contact": contact,
            "properties": properties,
        }
        self.logger.info("Call added %s %s (%s)", call_id, number or "unknown", direction)

    def _call_removed(self, call_path, reason):
        call_id = str(call_path)
        call = self.active_calls.pop(call_id, None)
        if not call:
            self.logger.warning("Unknown call removed: %s", call_id)
            return
        end = datetime.now()
        duration = int((end - call["start"]).total_seconds())
        payload = {
            "timestamp_start": call["start"].isoformat(),
            "timestamp_end": end.isoformat(),
            "duration_seconds": duration,
            "direction": call["properties"].get("State", "").upper() or call["direction"],
            "phone_number": call["number"],
            "contact_name": call["contact"],
            "device_id": DEVICE_ID,
            "user_id": USER_ID,
        }
        direction = "MISSED" if call["properties"].get("State") == "incoming" and duration < 2 else call["direction"]
        payload["direction"] = direction
        self.logger.info("Call finished %s (%ss) -> %s", call["number"] or "unknown", duration, direction)
        self._send_event(payload)

    def _send_event(self, payload: Dict):
        url = f"{API_BASE_URL}/events/phone"
        try:
            resp = self.session.post(url, json=payload, timeout=10)
            if resp.status_code >= 300:
                self.logger.error("API error %s: %s", resp.status_code, resp.text)
        except requests.RequestException as exc:
            self.logger.error("Could not send event: %s", exc)

    def stop(self, *_):
        self.logger.info("Stopping call logger")
        self.loop.quit()


def main():
    logger = CallLogger()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, logger.stop)
    logger.start()


if __name__ == "__main__":
    main()
