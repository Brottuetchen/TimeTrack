"""
Session-Routers - Alle Operationen lokal auf dem Pi.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession, joinedload

from ..database import get_db
from ..models import Session, Event, Assignment
from ..services.session_aggregator import aggregate_user_events
from ..services.assignment_rules import auto_apply_rules_to_session
from .. import schemas

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/aggregate", status_code=201)
def trigger_aggregation(
    user_id: str = Query(...),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: DBSession = Depends(get_db),
):
    """
    Triggert Session-Aggregation für einen User (lokal berechnet).
    Nützlich nach Import vieler Events oder manuell vom User getriggert.
    """
    if end:
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    else:
        end_dt = datetime.utcnow()

    if start:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    else:
        start_dt = end_dt - timedelta(days=7)  # Default: Letzte 7 Tage

    # Lösche alte Sessions im Zeitraum (Re-Aggregation)
    db.query(Session).filter(
        Session.user_id == user_id,
        Session.start_time >= start_dt,
        Session.end_time <= end_dt,
    ).delete()

    # Neue Sessions erstellen (lokal)
    sessions = aggregate_user_events(db, user_id, start_dt, end_dt)

    # Auto-apply rules to newly created sessions
    for session in sessions:
        auto_apply_rules_to_session(session, db)

    return {
        "sessions_created": len(sessions),
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
    }


@router.get("", response_model=List[schemas.SessionRead])
def list_sessions(
    user_id: Optional[str] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: DBSession = Depends(get_db),
):
    """
    Listet aggregierte Sessions (lokal gespeichert).
    """
    query = db.query(Session).options(
        joinedload(Session.assignment).joinedload(Assignment.project),
        joinedload(Session.assignment).joinedload(Assignment.milestone),
    )

    if user_id:
        query = query.filter(Session.user_id == user_id)
    if start:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        query = query.filter(Session.start_time >= start_dt)
    if end:
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        query = query.filter(Session.end_time <= end_dt)

    sessions = query.order_by(Session.start_time.desc()).offset(offset).limit(limit).all()

    # Convert assignment to proper format for response
    result = []
    for session in sessions:
        session_dict = {
            "id": session.id,
            "user_id": session.user_id,
            "process_name": session.process_name,
            "window_title_base": session.window_title_base,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "total_duration_seconds": session.total_duration_seconds,
            "active_duration_seconds": session.active_duration_seconds,
            "event_count": session.event_count,
            "break_count": session.break_count,
            "event_ids": session.event_ids,
            "is_private": session.is_private,
            "assignment_id": session.assignment_id,
            "assignment": None,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }
        result.append(session_dict)

    return result


@router.get("/{session_id}", response_model=schemas.SessionRead)
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    """Einzelne Session abrufen"""
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": session.id,
        "user_id": session.user_id,
        "process_name": session.process_name,
        "window_title_base": session.window_title_base,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "total_duration_seconds": session.total_duration_seconds,
        "active_duration_seconds": session.active_duration_seconds,
        "event_count": session.event_count,
        "break_count": session.break_count,
        "event_ids": session.event_ids,
        "is_private": session.is_private,
        "assignment_id": session.assignment_id,
        "assignment": None,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


@router.post("/{session_id}/assign")
def assign_session(
    session_id: int,
    payload: schemas.SessionAssignmentCreate,
    db: DBSession = Depends(get_db),
):
    """
    Weist eine komplette Session einem Projekt zu.
    Erstellt automatisch Assignments für ALLE Events der Session.
    """
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Assignment erstellen (für Session selbst)
    # Note: Assignment requires event_id, so we use the first event of the session
    if not session.event_ids:
        raise HTTPException(status_code=400, detail="Session has no events")

    first_event = db.get(Event, session.event_ids[0])
    if not first_event:
        raise HTTPException(status_code=400, detail="First event not found")

    assignment = Assignment(
        event_id=first_event.id,
        project_id=payload.project_id,
        milestone_id=payload.milestone_id,
        activity_type=payload.activity_type,
        comment=payload.comment,
    )
    db.add(assignment)
    db.flush()  # Um assignment.id zu bekommen

    session.assignment_id = assignment.id

    # Optional: Erstelle auch Assignments für einzelne Events
    # (falls User später auf Event-Level wechseln will)
    for event_id in session.event_ids[1:]:  # Skip first event (already assigned)
        # Check if event already has assignment
        existing = db.query(Assignment).filter(Assignment.event_id == event_id).first()
        if existing:
            continue

        event_assignment = Assignment(
            event_id=event_id,
            project_id=payload.project_id,
            milestone_id=payload.milestone_id,
            activity_type=payload.activity_type,
            comment=f"Auto-assigned from session {session_id}: {payload.comment}",
        )
        db.add(event_assignment)

    db.commit()
    db.refresh(session)

    return {
        "id": session.id,
        "user_id": session.user_id,
        "process_name": session.process_name,
        "window_title_base": session.window_title_base,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "total_duration_seconds": session.total_duration_seconds,
        "active_duration_seconds": session.active_duration_seconds,
        "event_count": session.event_count,
        "break_count": session.break_count,
        "event_ids": session.event_ids,
        "is_private": session.is_private,
        "assignment_id": session.assignment_id,
        "assignment": None,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }
