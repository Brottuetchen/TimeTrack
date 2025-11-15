from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..settings_store import load_settings, save_settings

router = APIRouter(prefix="/settings", tags=["settings"])


class LoggingSettingsUpdate(BaseModel):
    whitelist: Optional[List[str]] = None
    blacklist: Optional[List[str]] = None
    bluetooth_enabled: Optional[bool] = None


class PrivacyRequest(BaseModel):
    duration_minutes: Optional[int] = Field(None, ge=1, le=24 * 60)
    indefinite: bool = False


@router.get("/logging")
def get_logging_settings():
    settings = load_settings()
    return {
        **settings,
        "server_time": datetime.now(timezone.utc).isoformat(),
        "privacy_mode_until": settings.get("privacy_mode_until"),
    }


@router.put("/logging")
def update_logging_settings(payload: LoggingSettingsUpdate):
    settings = load_settings()
    if payload.whitelist is not None:
        settings["whitelist"] = [item.strip() for item in payload.whitelist if item.strip()]
    if payload.blacklist is not None:
        settings["blacklist"] = [item.strip() for item in payload.blacklist if item.strip()]
    if payload.bluetooth_enabled is not None:
        settings["bluetooth_enabled"] = payload.bluetooth_enabled
    save_settings(settings)
    return get_logging_settings()


@router.post("/privacy")
def activate_privacy(payload: PrivacyRequest):
    settings = load_settings()
    if payload.indefinite:
        settings["privacy_mode_until"] = "indefinite"
    elif payload.duration_minutes:
        until = datetime.now(timezone.utc) + timedelta(minutes=payload.duration_minutes)
        settings["privacy_mode_until"] = until.isoformat()
    else:
        raise HTTPException(status_code=400, detail="duration_minutes oder indefinite erforderlich")
    save_settings(settings)
    return get_logging_settings()


@router.post("/privacy/clear")
def clear_privacy():
    settings = load_settings()
    settings["privacy_mode_until"] = None
    save_settings(settings)
    return get_logging_settings()
