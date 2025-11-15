"""
Microsoft Teams integration via Graph API Call Records.
Uses App-Only authentication with MSAL to fetch call history.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models import CallDirection, CallLog, CallSource
from ..settings_store import load_settings


def get_teams_credentials() -> Dict[str, Optional[str]]:
    """
    Load Teams Graph API credentials from settings.

    Returns:
        Dict with tenant_id, client_id, client_secret.
    """
    settings = load_settings()
    return {
        "tenant_id": settings.get("teams_tenant_id"),
        "client_id": settings.get("teams_client_id"),
        "client_secret": settings.get("teams_client_secret"),
    }


async def acquire_graph_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    """
    Acquire an access token for Microsoft Graph using MSAL client credentials flow.

    Args:
        tenant_id: Azure AD tenant ID
        client_id: App registration client ID
        client_secret: App registration client secret

    Returns:
        Access token string

    Raises:
        Exception: If token acquisition fails

    TODO: Implement actual MSAL token acquisition:
        from msal import ConfidentialClientApplication
        app = ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" in result:
            return result["access_token"]
        raise Exception(f"Failed to acquire token: {result.get('error_description')}")
    """
    raise NotImplementedError("TODO: Install msal library and implement token acquisition")


async def fetch_graph_call_records(
    access_token: str,
    start: datetime,
    end: datetime
) -> List[Dict[str, Any]]:
    """
    Fetch call records from Microsoft Graph API for the given time range.

    Args:
        access_token: Valid Graph API access token
        start: Start of time range (inclusive)
        end: End of time range (exclusive)

    Returns:
        List of call record dictionaries from Graph API

    TODO: Implement actual Graph API call:
        - Endpoint: GET https://graph.microsoft.com/v1.0/communications/callRecords
        - Filter: $filter=startDateTime ge {start} and startDateTime lt {end}
        - Headers: Authorization: Bearer {access_token}
        - Handle pagination with @odata.nextLink
        - Example response structure:
          {
            "value": [
              {
                "id": "...",
                "startDateTime": "2025-11-15T10:00:00Z",
                "endDateTime": "2025-11-15T10:15:00Z",
                "participants": [...],
                "organizer": {...},
                ...
              }
            ]
          }
    """
    raise NotImplementedError("TODO: Install httpx/aiohttp and implement Graph API call")


def map_teams_callrecord_to_calllogs(record: Dict[str, Any], user_id: Optional[str] = None) -> List[CallLog]:
    """
    Map a Microsoft Teams call record to one or more CallLog entries.

    A single Teams call may involve multiple participants, so we create one CallLog
    per participant leg if needed, or a single entry for 1-1 calls.

    Args:
        record: Call record dictionary from Graph API
        user_id: Optional user ID to associate with the call log

    Returns:
        List of CallLog instances (not yet persisted to DB)

    Example record structure:
    {
        "id": "af8...",
        "version": 1,
        "type": "peer", # or "groupCall", "meeting"
        "startDateTime": "2025-11-15T10:00:00Z",
        "endDateTime": "2025-11-15T10:15:00Z",
        "organizer": {
            "user": {
                "id": "...",
                "displayName": "John Doe"
            }
        },
        "participants": [
            {
                "user": {
                    "id": "...",
                    "displayName": "Jane Smith"
                }
            }
        ]
    }
    """
    call_logs = []

    external_id = f"teams_{record.get('id', 'unknown')}"
    started_at = datetime.fromisoformat(record.get("startDateTime", "").replace("Z", "+00:00"))
    ended_at_str = record.get("endDateTime")
    ended_at = datetime.fromisoformat(ended_at_str.replace("Z", "+00:00")) if ended_at_str else None

    # Determine direction based on organizer vs participants
    # For simplicity, treat organizer as OUTBOUND and participants as INBOUND
    # In reality, this is more complex (may need to check if current user is organizer)
    call_type = record.get("type", "")

    # Get organizer info
    organizer = record.get("organizer", {}).get("user", {})
    organizer_name = organizer.get("displayName")
    organizer_id = organizer.get("id")

    # Get participants
    participants = record.get("participants", [])

    # For peer-to-peer calls, create one entry
    if call_type == "peer" and len(participants) == 1:
        participant = participants[0].get("user", {})
        remote_name = participant.get("displayName")
        remote_number = participant.get("id")  # Using user ID as "number"

        call_log = CallLog(
            user_id=user_id,
            source=CallSource.TEAMS,
            external_id=external_id,
            started_at=started_at,
            ended_at=ended_at,
            direction=CallDirection.OUTBOUND,  # TODO: Determine actual direction
            remote_number=remote_number,
            remote_name=remote_name,
            raw_payload=record,
        )
        call_logs.append(call_log)
    else:
        # For group calls/meetings, create one entry with organizer info
        call_log = CallLog(
            user_id=user_id,
            source=CallSource.TEAMS,
            external_id=external_id,
            started_at=started_at,
            ended_at=ended_at,
            direction=CallDirection.INTERNAL,  # Group calls are internal
            remote_number=organizer_id,
            remote_name=organizer_name or f"{len(participants)} participants",
            raw_payload=record,
        )
        call_logs.append(call_log)

    return call_logs


async def sync_teams_calls_for_timerange(
    db: Session,
    start: datetime,
    end: datetime,
    user_id: Optional[str] = None
) -> None:
    """
    Fetch Teams call records for the given time range and upsert into CallLog table.

    This function:
    1. Loads Teams credentials from settings
    2. Acquires a Graph API access token
    3. Fetches call records for the time range
    4. Maps each record to CallLog entries
    5. Upserts into database (based on external_id to avoid duplicates)

    Args:
        db: SQLAlchemy database session
        start: Start of time range (inclusive)
        end: End of time range (exclusive)
        user_id: Optional user ID to associate with call logs

    Raises:
        NotImplementedError: Token/API functions not yet implemented
        Exception: If credentials are missing or API calls fail
    """
    # Load credentials
    creds = get_teams_credentials()
    tenant_id = creds["tenant_id"]
    client_id = creds["client_id"]
    client_secret = creds["client_secret"]

    if not all([tenant_id, client_id, client_secret]):
        raise ValueError(
            "Teams credentials not configured. Please set teams_tenant_id, "
            "teams_client_id, and teams_client_secret in settings."
        )

    # Acquire access token
    access_token = await acquire_graph_token(tenant_id, client_id, client_secret)

    # Fetch call records
    records = await fetch_graph_call_records(access_token, start, end)

    # Map and upsert each record
    for record in records:
        call_logs = map_teams_callrecord_to_calllogs(record, user_id=user_id)

        for call_log in call_logs:
            # Check if already exists (based on source + external_id)
            existing = db.query(CallLog).filter(
                CallLog.source == call_log.source,
                CallLog.external_id == call_log.external_id
            ).first()

            if existing:
                # Update existing record
                existing.started_at = call_log.started_at
                existing.ended_at = call_log.ended_at
                existing.direction = call_log.direction
                existing.remote_number = call_log.remote_number
                existing.remote_name = call_log.remote_name
                existing.raw_payload = call_log.raw_payload
                existing.updated_at = datetime.utcnow()
            else:
                # Insert new record
                db.add(call_log)

        db.commit()
