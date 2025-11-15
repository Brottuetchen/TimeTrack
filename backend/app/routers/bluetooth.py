from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..bluetooth import (
    BluetoothError,
    connect_device,
    disconnect_device,
    list_devices,
    pair_device,
    pbap_sync,
    scan_devices,
)


router = APIRouter(prefix="/bluetooth", tags=["bluetooth"])


class MacPayload(BaseModel):
    mac: str


@router.get("/devices")
def devices():
    try:
        return {"devices": list_devices()}
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/scan")
def scan(timeout: int = Query(8, ge=3, le=30)):
    try:
        devices = scan_devices(timeout)
        return {"devices": devices}
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pair")
def pair(payload: MacPayload):
    try:
        stdout, stderr = pair_device(payload.mac)
        return {"stdout": stdout, "stderr": stderr}
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/connect")
def connect(payload: MacPayload):
    try:
        stdout, stderr = connect_device(payload.mac)
        return {"stdout": stdout, "stderr": stderr}
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/disconnect")
def disconnect(payload: MacPayload):
    try:
        stdout, stderr = disconnect_device(payload.mac)
        return {"stdout": stdout, "stderr": stderr}
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/pbap")
def trigger_pbap(payload: MacPayload):
    try:
        result = pbap_sync(payload.mac)
        return result
    except BluetoothError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
