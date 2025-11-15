"""
Placetel webhook integration for real-time call events.
Handles incoming webhook calls and maps them to CallLog entries.
"""
import hashlib
import hmac
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import CallDirection, CallLog, CallSource
from ..settings_store import load_settings


def verify_placetel_signature(payload: bytes, signature: str) -> bool:
    """
    Verify the webhook signature from Placetel.

    Args:
        payload: Raw request body as bytes
        signature: Signature header from Placetel (e.g., X-Placetel-Signature)

    Returns:
        True if signature is valid, False otherwise

    TODO: Implement actual signature verification:
        shared_secret = load_settings().get("placetel_shared_secret")
        if not shared_secret:
            return False
        expected = hmac.new(
            shared_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    """
    # For now, accept all requests (insecure - implement signature check in production)
    shared_secret = load_settings().get("placetel_shared_secret")
    if not shared_secret:
        # If no secret configured, skip validation (dev mode)
        return True

    # TODO: Implement actual HMAC signature verification
    return True


def map_placetel_direction(event_type: str) -> Optional[CallDirection]:
    """
    Map Placetel event type to CallDirection enum.

    Args:
        event_type: Placetel event type (e.g., "CallCreated", "CallAnswered", "CallHungup")

    Returns:
        CallDirection or None

    Placetel typically sends:
    - "inbound" or "external" for incoming calls
    - "outbound" for outgoing calls
    - "internal" for internal calls
    """
    if not event_type:
        return None

    event_lower = event_type.lower()

    if "inbound" in event_lower or "external" in event_lower:
        return CallDirection.INBOUND
    elif "outbound" in event_lower:
        return CallDirection.OUTBOUND
    elif "internal" in event_lower:
        return CallDirection.INTERNAL

    return None


def apply_placetel_event_to_calllog(db: Session, payload: Dict[str, Any]) -> CallLog:
    """
    Create or update a CallLog entry based on a Placetel webhook event.

    Placetel sends multiple events for a single call session:
    - Ringing: Call is initiated
    - Connected: Call is answered
    - Hangup: Call is ended

    We use the call_id (or similar unique identifier) to update the same CallLog
    across these events.

    Args:
        db: SQLAlchemy database session
        payload: Webhook payload dictionary

    Returns:
        The created or updated CallLog instance

    Example payload structure (actual structure varies by Placetel API version):
    {
        "event": "CallCreated",  # or "CallAnswered", "CallHungup"
        "call_id": "abc123",
        "type": "inbound",  # or "outbound", "internal"
        "from": "+491234567890",
        "from_name": "John Doe",
        "to": "+490987654321",
        "to_name": "Jane Smith",
        "timestamp": "2025-11-15T10:00:00Z",
        "duration": 120  # Only present on hangup
    }
    """
    # Extract fields from payload
    event_type = payload.get("event", "")
    call_id = payload.get("call_id") or payload.get("id")

    if not call_id:
        raise ValueError("Placetel webhook payload missing call_id or id")

    external_id = f"placetel_{call_id}"

    # Determine direction
    call_type = payload.get("type", "")
    direction = map_placetel_direction(call_type)

    # Extract caller/callee info
    from_number = payload.get("from")
    from_name = payload.get("from_name")
    to_number = payload.get("to")
    to_name = payload.get("to_name")

    # For inbound calls, remote is "from"; for outbound, remote is "to"
    if direction == CallDirection.INBOUND:
        remote_number = from_number
        remote_name = from_name
    else:
        remote_number = to_number
        remote_name = to_name

    # Parse timestamp
    timestamp_str = payload.get("timestamp") or payload.get("time")
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            timestamp = datetime.utcnow()
    else:
        timestamp = datetime.utcnow()

    # Check for existing call log
    existing = db.query(CallLog).filter(
        CallLog.source == CallSource.PLACETEL,
        CallLog.external_id == external_id
    ).first()

    if existing:
        # Update existing record
        if event_type.lower() in ["callhungup", "callended", "hangup"]:
            # This is the final event - set end time and duration
            existing.ended_at = timestamp
        elif event_type.lower() in ["callanswered", "callconnected", "connected"]:
            # Call was answered - update started_at if not set
            if not existing.started_at or existing.started_at > timestamp:
                existing.started_at = timestamp

        # Always update raw_payload with latest event
        if existing.raw_payload:
            # Append to history
            if "events" not in existing.raw_payload:
                existing.raw_payload["events"] = []
            existing.raw_payload["events"].append(payload)
        else:
            existing.raw_payload = {"events": [payload]}

        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new call log
        # For initial events (Ringing), we might not have an end time yet
        started_at = timestamp
        ended_at = None

        if event_type.lower() in ["callhungup", "callended", "hangup"]:
            # If first event is already a hangup, use timestamp as end
            ended_at = timestamp

        call_log = CallLog(
            user_id=None,  # TODO: Map Placetel user to TimeTrack user_id
            source=CallSource.PLACETEL,
            external_id=external_id,
            started_at=started_at,
            ended_at=ended_at,
            direction=direction,
            remote_number=remote_number,
            remote_name=remote_name,
            raw_payload={"events": [payload]},
        )

        db.add(call_log)
        db.commit()
        db.refresh(call_log)
        return call_log
