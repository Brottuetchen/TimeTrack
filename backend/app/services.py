"""
Service layer functions for business logic and data access.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from .models import CallLog, CallSource


def get_calllogs_for_user_and_range(
    db: Session,
    user_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    source: Optional[CallSource] = None
) -> List[CallLog]:
    """
    Retrieve call logs for a specific user within a time range.

    Args:
        db: SQLAlchemy database session
        user_id: Optional user ID to filter by (if None, returns all users)
        start: Optional start datetime (inclusive)
        end: Optional end datetime (exclusive)
        source: Optional CallSource to filter by specific integration

    Returns:
        List of CallLog instances ordered by started_at descending
    """
    query = db.query(CallLog)

    if user_id is not None:
        query = query.filter(CallLog.user_id == user_id)

    if start is not None:
        query = query.filter(CallLog.started_at >= start)

    if end is not None:
        query = query.filter(CallLog.started_at < end)

    if source is not None:
        query = query.filter(CallLog.source == source)

    # Order by most recent first
    query = query.order_by(CallLog.started_at.desc())

    return query.all()


def upsert_calllog(
    db: Session,
    source: CallSource,
    external_id: str,
    started_at: datetime,
    ended_at: Optional[datetime] = None,
    user_id: Optional[str] = None,
    direction: Optional[str] = None,
    remote_number: Optional[str] = None,
    remote_name: Optional[str] = None,
    raw_payload: Optional[dict] = None
) -> CallLog:
    """
    Create or update a CallLog entry based on source and external_id.

    Args:
        db: SQLAlchemy database session
        source: Call source (BLUETOOTH_PBAP, TEAMS, PLACETEL, MANUAL)
        external_id: Unique identifier from the source system
        started_at: Call start timestamp
        ended_at: Optional call end timestamp
        user_id: Optional user identifier
        direction: Optional call direction
        remote_number: Optional remote party number/ID
        remote_name: Optional remote party display name
        raw_payload: Optional raw event data

    Returns:
        The created or updated CallLog instance
    """
    existing = db.query(CallLog).filter(
        CallLog.source == source,
        CallLog.external_id == external_id
    ).first()

    if existing:
        # Update existing
        existing.started_at = started_at
        existing.ended_at = ended_at
        existing.user_id = user_id
        existing.direction = direction
        existing.remote_number = remote_number
        existing.remote_name = remote_name
        existing.raw_payload = raw_payload
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        call_log = CallLog(
            source=source,
            external_id=external_id,
            started_at=started_at,
            ended_at=ended_at,
            user_id=user_id,
            direction=direction,
            remote_number=remote_number,
            remote_name=remote_name,
            raw_payload=raw_payload,
        )
        db.add(call_log)
        db.commit()
        db.refresh(call_log)
        return call_log
