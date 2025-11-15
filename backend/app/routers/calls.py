"""
API router for unified call log management.
Provides endpoints for retrieving, creating, and managing call logs from all sources.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Header, Query, Request
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..integrations.placetel import apply_placetel_event_to_calllog, verify_placetel_signature
from ..integrations.teams import sync_teams_calls_for_timerange
from ..models import CallSource
from ..services import get_calllogs_for_user_and_range

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("", response_model=List[schemas.CallLogRead])
def list_call_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start: Optional[datetime] = Query(None, description="Start datetime (ISO8601)"),
    end: Optional[datetime] = Query(None, description="End datetime (ISO8601)"),
    source: Optional[CallSource] = Query(None, description="Filter by call source"),
    db: Session = Depends(get_db)
):
    """
    Retrieve call logs with optional filters.

    Query parameters:
    - user_id: Filter calls for a specific user
    - start: Filter calls starting from this datetime (inclusive)
    - end: Filter calls ending before this datetime (exclusive)
    - source: Filter by specific call source (bluetooth_pbap, teams, placetel, manual)

    Returns:
    - List of call logs ordered by started_at (most recent first)
    """
    call_logs = get_calllogs_for_user_and_range(
        db=db,
        user_id=user_id,
        start=start,
        end=end,
        source=source
    )
    return call_logs


@router.post("", response_model=schemas.CallLogRead, status_code=201)
def create_call_log(
    call_log_data: schemas.CallLogCreate,
    db: Session = Depends(get_db)
):
    """
    Manually create a new call log entry.

    Useful for:
    - Manual call logging
    - Importing historical data
    - Testing

    Request body should include all required CallLog fields.
    """
    from ..models import CallLog

    # Check for duplicate based on source + external_id
    existing = db.query(CallLog).filter(
        CallLog.source == call_log_data.source,
        CallLog.external_id == call_log_data.external_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"CallLog with source={call_log_data.source} and external_id={call_log_data.external_id} already exists"
        )

    call_log = CallLog(**call_log_data.dict())
    db.add(call_log)
    db.commit()
    db.refresh(call_log)
    return call_log


@router.get("/{call_log_id}", response_model=schemas.CallLogRead)
def get_call_log(call_log_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific call log by ID.
    """
    from ..models import CallLog

    call_log = db.query(CallLog).filter(CallLog.id == call_log_id).first()
    if not call_log:
        raise HTTPException(status_code=404, detail="CallLog not found")
    return call_log


@router.post("/sync/teams")
async def sync_teams_calls(
    start: datetime = Query(..., description="Start datetime (ISO8601)"),
    end: datetime = Query(..., description="End datetime (ISO8601)"),
    user_id: Optional[str] = Query(None, description="User ID to associate with calls"),
    db: Session = Depends(get_db)
):
    """
    Trigger a manual sync of Microsoft Teams call records for a given time range.

    This endpoint fetches call records from Microsoft Graph API and upserts them
    into the CallLog table.

    Note: Requires Teams credentials to be configured in settings.

    Query parameters:
    - start: Start of time range (inclusive)
    - end: End of time range (exclusive)
    - user_id: Optional user ID to associate with the synced calls

    Returns:
    - Success message with sync details
    """
    try:
        await sync_teams_calls_for_timerange(db=db, start=start, end=end, user_id=user_id)
        return {
            "status": "success",
            "message": f"Teams calls synced for range {start.isoformat()} to {end.isoformat()}",
            "start": start.isoformat(),
            "end": end.isoformat()
        }
    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail=f"Teams integration not fully implemented: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync Teams calls: {str(e)}"
        )


@router.post("/webhooks/placetel")
async def placetel_webhook(
    request: Request,
    x_placetel_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for Placetel call events.

    Placetel sends real-time call events (Ringing, Connected, Hangup) to this endpoint.
    We verify the signature (if configured) and create/update CallLog entries.

    Headers:
    - X-Placetel-Signature: HMAC signature for request verification (optional)

    Request body: JSON payload from Placetel webhook

    Returns:
    - Success message with call log ID
    """
    # Read raw body for signature verification
    body = await request.body()

    # Verify signature if provided
    if x_placetel_signature:
        if not verify_placetel_signature(body, x_placetel_signature):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {str(e)}")

    # Apply event to call log
    try:
        call_log = apply_placetel_event_to_calllog(db=db, payload=payload)
        return {
            "status": "success",
            "message": "Placetel event processed",
            "call_log_id": call_log.id,
            "event": payload.get("event", "unknown")
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process Placetel event: {str(e)}"
        )
