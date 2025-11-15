import json
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests


class PBAPSync:
    def __init__(
        self,
        device_mac: str,
        api_base: str,
        session: requests.Session,
        device_id: str,
        user_id: str,
        state_path: Path,
        interval_seconds: int,
        logger,
    ):
        self.device_mac = device_mac
        self.api_base = api_base.rstrip("/")
        self.session = session
        self.device_id = device_id
        self.user_id = user_id
        self.state_path = state_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.interval = max(60, interval_seconds)
        self.logger = logger
        self.seen = self._load_state()

    def run(self):
        while True:
            try:
                self.sync_once()
            except Exception as exc:  # pragma: no cover
                self.logger.error("PBAP sync failed: %s", exc)
            time.sleep(self.interval)

    def sync_once(self):
        tmp_vcf = Path(tempfile.gettempdir()) / "timetrack_callhistory.vcf"
        if not self._download_vcf(tmp_vcf):
            return
        entries = self._parse_vcf(tmp_vcf)
        new_entries = [entry for entry in entries if entry["uid"] not in self.seen]
        if not new_entries:
            self.logger.debug("PBAP sync: keine neuen Einträge")
            return
        for entry in new_entries:
            if self._send_entry(entry):
                self.seen.add(entry["uid"])
        self._save_state()
        self.logger.info("PBAP sync: %s neue Einträge übertragen", len(new_entries))

    def _download_vcf(self, target: Path) -> bool:
        cmd = (
            f"printf 'connect {self.device_mac} PBAP\\n"
            f"get telecom/callhistory.vcf {target}\\n"
            "quit\\n' | obexctl"
        )
        result = subprocess.run(
            ["/bin/bash", "-lc", cmd],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            self.logger.debug("PBAP download failed: %s %s", result.stdout.strip(), result.stderr.strip())
            return False
        if not target.exists():
            self.logger.debug("PBAP download delivered no file")
            return False
        return True

    def _parse_vcf(self, path: Path) -> List[Dict]:
        entries = []
        current: Dict[str, str] = {}
        for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if line.startswith("BEGIN:VCARD"):
                current = {}
            elif line.startswith("END:VCARD"):
                if current.get("datetime") and current.get("number"):
                    entries.append(current.copy())
            elif line.startswith("TEL"):
                _, value = line.split(":", 1)
                current["number"] = value.strip()
            elif line.startswith("X-IRMC-CALL-DATETIME"):
                _, value = line.split(":", 1)
                current["datetime"] = value.strip()
            elif line.startswith("X-IRMC-CL") or line.startswith("X-IRMC-CALL-TYPE"):
                _, value = line.split(":", 1)
                current["call_type"] = value.strip().upper()
            elif line.startswith("N:"):
                _, value = line.split(":", 1)
                current["contact"] = value.split(";")[0]
        normalized = []
        for entry in entries:
            dt = self._parse_datetime(entry["datetime"])
            if not dt:
                continue
            uid = f"{entry['number']}_{entry.get('call_type','')}_{dt.isoformat()}"
            normalized.append(
                {
                    "uid": uid,
                    "timestamp": dt,
                    "number": entry["number"],
                    "contact": entry.get("contact", ""),
                    "call_type": entry.get("call_type", ""),
                }
            )
        normalized.sort(key=lambda e: e["timestamp"])
        return normalized

    def _parse_datetime(self, value: str) -> Optional[datetime]:
        fmt_candidates = ["%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S"]
        for fmt in fmt_candidates:
            try:
                dt = datetime.strptime(value, fmt)
                return dt
            except ValueError:
                continue
        return None

    def _send_entry(self, entry: Dict) -> bool:
        direction = self._map_direction(entry["call_type"])
        payload = {
            "timestamp_start": entry["timestamp"].isoformat(),
            "timestamp_end": entry["timestamp"].isoformat(),
            "direction": direction,
            "phone_number": entry["number"],
            "contact_name": entry.get("contact") or None,
            "device_id": self.device_id,
            "user_id": self.user_id,
        }
        try:
            resp = self.session.post(f"{self.api_base}/events/phone", json=payload, timeout=10)
            if resp.status_code >= 300:
                self.logger.warning("PBAP upload failed (%s): %s", resp.status_code, resp.text)
                return False
            return True
        except requests.RequestException as exc:
            self.logger.warning("PBAP upload exception: %s", exc)
            return False

    def _map_direction(self, call_type: str) -> str:
        normalized = call_type.upper()
        if normalized in {"INCOMING", "RECEIVED"}:
            return "INCOMING"
        if normalized in {"OUTGOING", "DIALED", "DIALED_CALL"}:
            return "OUTGOING"
        if normalized in {"MISSED"}:
            return "MISSED"
        return "OUTGOING"

    def _load_state(self) -> set:
        if not self.state_path.exists():
            return set()
        try:
            return set(json.loads(self.state_path.read_text()))
        except json.JSONDecodeError:
            return set()

    def _save_state(self):
        self.state_path.write_text(json.dumps(sorted(self.seen)), encoding="utf-8")
