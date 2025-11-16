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
    # Call Sync Settings
    teams_tenant_id: Optional[str] = None
    teams_client_id: Optional[str] = None
    teams_client_secret: Optional[str] = None
    placetel_shared_secret: Optional[str] = None


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
    # Call Sync Settings
    if payload.teams_tenant_id is not None:
        settings["teams_tenant_id"] = payload.teams_tenant_id.strip() if payload.teams_tenant_id else None
    if payload.teams_client_id is not None:
        settings["teams_client_id"] = payload.teams_client_id.strip() if payload.teams_client_id else None
    if payload.teams_client_secret is not None:
        settings["teams_client_secret"] = payload.teams_client_secret.strip() if payload.teams_client_secret else None
    if payload.placetel_shared_secret is not None:
        settings["placetel_shared_secret"] = payload.placetel_shared_secret.strip() if payload.placetel_shared_secret else None
    save_settings(settings)
    return get_logging_settings()


@router.post("/logging")
def update_logging_settings_post(payload: dict):
    """
    POST-Alternative für Windows Agent CallSyncManager.
    Akzeptiert vollständiges Settings-Dict und merged es.
    """
    settings = load_settings()
    # Merge übergebene Settings
    settings.update(payload)
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


@router.get("/logo")
def get_logo():
    """
    Gibt das hochgeladene SVG-Logo zurück.
    """
    settings = load_settings()
    return {"logo_svg": settings.get("logo_svg", None)}


@router.put("/logo")
def upload_logo(payload: dict):
    """
    Speichert ein SVG-Logo.
    """
    settings = load_settings()
    logo_svg = payload.get("logo_svg", "")

    # Validierung: Maximal 500 KB
    if len(logo_svg) > 500 * 1024:
        raise HTTPException(status_code=400, detail="Logo zu groß (max. 500 KB)")

    # Einfache SVG-Validierung
    if logo_svg:
        stripped = logo_svg.strip()
        if not (stripped.startswith("<svg") or stripped.startswith("<?xml")):
            raise HTTPException(status_code=400, detail="Ungültiges SVG-Format")

    settings["logo_svg"] = logo_svg
    save_settings(settings)
    return {"logo_svg": logo_svg}


@router.delete("/logo")
def delete_logo():
    """
    Entfernt das hochgeladene Logo.
    """
    settings = load_settings()
    settings["logo_svg"] = None
    save_settings(settings)
    return {"logo_svg": None}


@router.get("/agent-config")
def get_agent_config():
    """
    Gibt eine komplette Agent-Konfiguration im config.json-Format zurück.
    Merged Remote-Settings (whitelist/blacklist) mit Default-Config.

    Diese Config kann vom User heruntergeladen und als config.json im Agent-Verzeichnis gespeichert werden.
    """
    settings = load_settings()

    # Remote-Filter aus Settings holen
    remote_whitelist = settings.get("whitelist", [])
    remote_blacklist = settings.get("blacklist", [])

    # Standard-Config mit Remote-Filtern
    agent_config = {
        "base_url": "http://localhost:8000",
        "machine_id": "auto-detect",  # Agent generiert automatisch eine machine_id beim Start
        "user_id": "BITTE_EINTRAGEN",  # User muss dies anpassen
        "poll_interval_ms": 1500,
        "send_batch_seconds": 30,
        "include_processes": [],  # Leer, wenn Remote-Whitelist verwendet wird
        "exclude_processes": remote_blacklist,  # Remote-Blacklist übernehmen
        "include_title_keywords": [],
        "exclude_title_keywords": [],
        "buffer_file": "%APPDATA%\\TimeTrack\\buffer.json",
        "log_file": "%APPDATA%\\TimeTrack\\timetrack_agent.log",
        "verify_ssl": False,
        "api_key": None,
        "settings_poll_seconds": 60,
        # Call Sync Settings
        "call_sync_enabled": False,
        "call_sync_interval_minutes": 15,
        "teams_enabled": False,
        "teams_tenant_id": settings.get("teams_tenant_id"),
        "teams_client_id": settings.get("teams_client_id"),
        "teams_client_secret": settings.get("teams_client_secret"),
        "placetel_enabled": False,
        "placetel_api_key": None,
        "placetel_api_url": "https://api.placetel.de/v2",
        # Info-Felder (nicht von Agent verwendet, nur zur Info)
        "_info": {
            "remote_whitelist": remote_whitelist,
            "remote_blacklist": remote_blacklist,
            "note": "Remote filters from Web-UI have priority over local filters. include_processes is empty because remote whitelist is managed via Web-UI."
        }
    }

    return agent_config
