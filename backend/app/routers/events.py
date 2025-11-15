from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import Event, SourceType

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/phone", response_model=schemas.EventRead, status_code=201)
def create_phone_event(payload: schemas.PhoneEventCreate, db: Session = Depends(get_db)):
    event = Event(
        source_type=SourceType.PHONE,
        timestamp_start=payload.timestamp_start,
        timestamp_end=payload.timestamp_end,
        duration_seconds=_resolve_duration(payload.timestamp_start, payload.timestamp_end, payload.duration_seconds),
        phone_number=payload.phone_number,
        contact_name=payload.contact_name,
        direction=payload.direction,
        machine_id=payload.machine_id,
        device_id=payload.device_id,
        user_id=payload.user_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/window", response_model=schemas.EventRead, status_code=201)
def create_window_event(payload: schemas.WindowEventCreate, db: Session = Depends(get_db)):
    event = Event(
        source_type=SourceType.WINDOW,
        timestamp_start=payload.timestamp_start,
        timestamp_end=payload.timestamp_end,
        duration_seconds=_resolve_duration(payload.timestamp_start, payload.timestamp_end, payload.duration_seconds),
        window_title=payload.window_title,
        process_name=payload.process_name,
        machine_id=payload.machine_id,
        device_id=payload.device_id,
        user_id=payload.user_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("", response_model=List[schemas.EventRead])
def list_events(
    start: Optional[datetime] = Query(None, description="Filter events starting after this timestamp"),
    end: Optional[datetime] = Query(None, description="Filter events ending before this timestamp"),
    user_id: Optional[str] = Query(None),
    source_type: Optional[SourceType] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Event)

    if start:
        query = query.filter(
            or_(
                Event.timestamp_start >= start,
                and_(Event.timestamp_end.isnot(None), Event.timestamp_end >= start),
            )
        )
    if end:
        query = query.filter(Event.timestamp_start <= end)
    if user_id:
        query = query.filter(Event.user_id == user_id)
    if source_type:
        query = query.filter(Event.source_type == source_type)

    events = query.order_by(Event.timestamp_start.desc()).offset(offset).limit(limit).all()
    return events


def _resolve_duration(start: datetime, end: Optional[datetime], duration_seconds: Optional[int]) -> Optional[int]:
    if duration_seconds is not None:
        return duration_seconds
    if start and end:
        return int((end - start).total_seconds())
    return None
