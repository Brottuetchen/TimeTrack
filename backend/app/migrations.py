"""
Data migration helpers for CallLog system.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from .models import CallDirection, CallLog, CallSource, Event, SourceType


def migrate_events_to_calllogs(db: Session, dry_run: bool = False) -> dict:
    """
    Migrate existing phone events from the Event table to the CallLog table.

    This function:
    1. Queries all phone events from the Event table
    2. Maps each event to a CallLog entry with source=BLUETOOTH_PBAP
    3. Creates CallLog entries if they don't already exist

    Args:
        db: SQLAlchemy database session
        dry_run: If True, only count events that would be migrated without actually migrating

    Returns:
        Dictionary with migration statistics:
        {
            "total_phone_events": int,
            "migrated": int,
            "skipped": int,
            "errors": int
        }
    """
    stats = {
        "total_phone_events": 0,
        "migrated": 0,
        "skipped": 0,
        "errors": 0
    }

    # Query all phone events
    phone_events = db.query(Event).filter(Event.source_type == SourceType.PHONE).all()
    stats["total_phone_events"] = len(phone_events)

    for event in phone_events:
        try:
            # Generate external_id from Event.id
            external_id = f"bluetooth_event_{event.id}"

            # Check if already migrated
            existing = db.query(CallLog).filter(
                CallLog.source == CallSource.BLUETOOTH_PBAP,
                CallLog.external_id == external_id
            ).first()

            if existing:
                stats["skipped"] += 1
                continue

            if dry_run:
                stats["migrated"] += 1
                continue

            # Map Event.direction to CallDirection
            direction = None
            if event.direction == CallDirection.INCOMING:
                direction = CallDirection.INBOUND
            elif event.direction == CallDirection.OUTGOING:
                direction = CallDirection.OUTBOUND
            elif event.direction == CallDirection.MISSED:
                # Missed calls are typically inbound that weren't answered
                direction = CallDirection.INBOUND

            # Create CallLog entry
            call_log = CallLog(
                user_id=event.user_id,
                source=CallSource.BLUETOOTH_PBAP,
                external_id=external_id,
                started_at=event.timestamp_start,
                ended_at=event.timestamp_end,
                direction=direction,
                remote_number=event.phone_number,
                remote_name=event.contact_name,
                raw_payload={
                    "migrated_from_event_id": event.id,
                    "original_direction": event.direction.value if event.direction else None,
                    "machine_id": event.machine_id,
                    "device_id": event.device_id,
                    "is_private": event.is_private,
                    "duration_seconds": event.duration_seconds
                }
            )

            db.add(call_log)
            stats["migrated"] += 1

        except Exception as e:
            stats["errors"] += 1
            print(f"Error migrating event {event.id}: {e}")

    if not dry_run:
        db.commit()

    return stats


def auto_migrate_on_startup(db: Session) -> None:
    """
    Automatically run migrations on startup if needed.

    This is called from database.py init_db() to ensure data is migrated
    when the CallLog table is first created.

    Args:
        db: SQLAlchemy database session
    """
    # Check if CallLog table has any entries
    call_log_count = db.query(CallLog).count()

    # Check if Event table has phone events
    phone_event_count = db.query(Event).filter(Event.source_type == SourceType.PHONE).count()

    # If CallLog is empty but we have phone events, run migration
    if call_log_count == 0 and phone_event_count > 0:
        print(f"Running automatic migration: {phone_event_count} phone events -> CallLog")
        stats = migrate_events_to_calllogs(db, dry_run=False)
        print(f"Migration complete: {stats}")
