import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

SETTINGS_PATH = Path(__file__).resolve().parents[1] / "logging_settings.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "privacy_mode_until": None,
    "whitelist": [],
    "blacklist": [],
    "bluetooth_enabled": True,
}


def load_settings() -> Dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return DEFAULT_SETTINGS.copy()
    try:
        data = json.loads(SETTINGS_PATH.read_text())
    except json.JSONDecodeError:
        return DEFAULT_SETTINGS.copy()
    merged = {**DEFAULT_SETTINGS, **data}
    _auto_clear_privacy(merged)
    return merged


def save_settings(settings: Dict[str, Any]) -> None:
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def _auto_clear_privacy(settings: Dict[str, Any]) -> None:
    """If privacy_mode_until is in the past, reset it."""
    until = settings.get("privacy_mode_until")
    if not until:
        return
    if isinstance(until, str) and until.lower() == "indefinite":
        return
    try:
        ts = datetime.fromisoformat(until)
    except ValueError:
        return
    if ts <= datetime.now(timezone.utc):
        settings["privacy_mode_until"] = None
