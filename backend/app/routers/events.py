from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..models import Event, SourceType, Assignment

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


@router.patch("/{event_id}", response_model=schemas.EventRead)
def update_event(event_id: int, payload: schemas.EventUpdate, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if payload.is_private is not None:
        event.is_private = payload.is_private
    db.commit()
    db.refresh(event)
    return event


@router.patch("/bulk", response_model=schemas.BulkEventResponse)
def bulk_update_events(payload: schemas.BulkEventUpdate, db: Session = Depends(get_db)):
    """
    Bulk-Update für Events:
    - is_private: Privacy-Flag setzen (True/False)
    - delete: Events löschen
    - unassign: Assignments entfernen
    """
    if not payload.event_ids:
        raise HTTPException(status_code=400, detail="event_ids darf nicht leer sein")

    # Events laden
    events = db.query(Event).filter(Event.id.in_(payload.event_ids)).all()
    found_ids = {e.id for e in events}

    # Nicht gefundene IDs
    missing_ids = set(payload.event_ids) - found_ids
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Events nicht gefunden: {sorted(missing_ids)}"
        )

    updated_count = 0
    deleted_count = 0
    unassigned_count = 0

    # DELETE Operation
    if payload.delete:
        # Assignments zuerst löschen (FK-Constraint)
        assignment_count = db.query(Assignment).filter(
            Assignment.event_id.in_(payload.event_ids)
        ).delete(synchronize_session=False)
        unassigned_count += assignment_count

        # Events löschen
        deleted_count = db.query(Event).filter(
            Event.id.in_(payload.event_ids)
        ).delete(synchronize_session=False)

        db.commit()

        return schemas.BulkEventResponse(
            updated_count=0,
            deleted_count=deleted_count,
            unassigned_count=unassigned_count,
            event_ids=payload.event_ids
        )

    # UNASSIGN Operation
    if payload.unassign:
        unassigned_count = db.query(Assignment).filter(
            Assignment.event_id.in_(payload.event_ids)
        ).delete(synchronize_session=False)

    # PRIVACY Operation
    if payload.is_private is not None:
        for event in events:
            event.is_private = payload.is_private
            updated_count += 1

    db.commit()

    return schemas.BulkEventResponse(
        updated_count=updated_count,
        deleted_count=deleted_count,
        unassigned_count=unassigned_count,
        event_ids=payload.event_ids
    )


@router.get("/unassigned", response_model=List[schemas.EventRead])
def list_unassigned_events(
    user_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Liste von Events ohne Assignment.
    Wird für Quick-Assign Dialog verwendet.
    """
    # Subquery: Event-IDs mit Assignment
    assigned_event_ids = db.query(Assignment.event_id).distinct()

    # Query: Events ohne Assignment
    query = db.query(Event).filter(~Event.id.in_(assigned_event_ids))

    if user_id:
        query = query.filter(Event.user_id == user_id)

    events = query.order_by(Event.timestamp_start.desc()).offset(offset).limit(limit).all()
    return events


def _resolve_duration(start: datetime, end: Optional[datetime], duration_seconds: Optional[int]) -> Optional[int]:
    if duration_seconds is not None:
        return duration_seconds
    if start and end:
        return int((end - start).total_seconds())
    return None
