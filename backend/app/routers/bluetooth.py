from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..bluetooth import (
    BluetoothError,
    connect_device,
    disconnect_device,
    list_devices,
    pair_device,
    pbap_sync,
    remove_device,
    scan_devices,
)
from ..bluetooth_agent import allow_incoming_pair, incoming_status


router = APIRouter(prefix="/bluetooth", tags=["bluetooth"])


class MacPayload(BaseModel):
    mac: str


class IncomingPayload(BaseModel):
    mac: str
    duration: int | None = 60


@router.get("/devices")
def devices():
    try:
        return {"devices": list_devices()}
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/scan")
def scan(timeout: int = Query(8, ge=3, le=30)):
    try:
        result = scan_devices(timeout)
        return result
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pair")
def pair(payload: MacPayload):
    try:
        code, stdout, stderr = pair_device(payload.mac)
        return {"returncode": code, "stdout": stdout, "stderr": stderr}
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/connect")
def connect(payload: MacPayload):
    try:
        code, stdout, stderr = connect_device(payload.mac)
        return {"returncode": code, "stdout": stdout, "stderr": stderr}
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/disconnect")
def disconnect(payload: MacPayload):
    try:
        code, stdout, stderr = disconnect_device(payload.mac)
        return {"returncode": code, "stdout": stdout, "stderr": stderr}
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/remove")
def remove(payload: MacPayload):
    try:
        code, stdout, stderr = remove_device(payload.mac)
        return {"returncode": code, "stdout": stdout, "stderr": stderr}
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pbap")
def trigger_pbap(payload: MacPayload):
    try:
        result = pbap_sync(payload.mac)
        return result
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/incoming")
def allow_incoming(payload: IncomingPayload):
    duration = payload.duration or 60
    if duration < 5 or duration > 300:
        raise HTTPException(status_code=400, detail="Duration must be between 5 and 300 seconds")
    try:
        expires_at = allow_incoming_pair(payload.mac, duration)
        return {"expires_at": expires_at, "mac": payload.mac.upper(), "duration": duration}
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/incoming/status")
def incoming_pairing_status():
    return incoming_status()
