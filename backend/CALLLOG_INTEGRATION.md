# CallLog Integration Guide

## Overview

The TimeTrack backend now includes a unified **CallLog** system that consolidates call data from multiple sources:

- **Bluetooth/PBAP**: Existing phone call events from Bluetooth devices
- **Microsoft Teams**: Call records from Teams via Graph API
- **Placetel**: Real-time call events via webhooks
- **Manual**: Manually created call entries

All call data is stored in a single `calllogs` table with source tracking and deduplication.

## Architecture

### Database Model

**CallLog** table ([models.py:97-115](backend/app/models.py#L97-L115)):
```python
class CallLog(Base):
    id: int (Primary Key)
    user_id: str (nullable, indexed)
    source: CallSource (BLUETOOTH_PBAP | TEAMS | PLACETEL | MANUAL)
    external_id: str (indexed, unique per source)
    started_at: datetime (indexed)
    ended_at: datetime (nullable)
    direction: CallDirection (INBOUND | OUTBOUND | INTERNAL | nullable)
    remote_number: str (nullable)
    remote_name: str (nullable)
    raw_payload: JSON (nullable)
    created_at: datetime
    updated_at: datetime
```

**Indexes**:
- `user_id` - Fast filtering by user
- `source` - Fast filtering by integration source
- `external_id` - Fast upsert/deduplication
- `started_at` - Fast time range queries

### Enums

**CallSource** ([models.py:25-29](backend/app/models.py#L25-L29)):
- `bluetooth_pbap` - Bluetooth/PBAP synced calls
- `teams` - Microsoft Teams calls
- `placetel` - Placetel telephony system calls
- `manual` - Manually created entries

**CallDirection** ([models.py:16-22](backend/app/models.py#L16-L22)):
- `INBOUND` / `INCOMING` - Incoming calls
- `OUTBOUND` / `OUTGOING` - Outgoing calls
- `INTERNAL` - Internal calls (group/meetings)
- `MISSED` - Missed calls (legacy, maps to INBOUND)

## API Endpoints

All endpoints are under `/calls` prefix.

### 1. List Call Logs

**GET** `/calls`

Query parameters:
- `user_id` (optional): Filter by user ID
- `start` (optional): ISO8601 datetime - filter calls starting from this time (inclusive)
- `end` (optional): ISO8601 datetime - filter calls ending before this time (exclusive)
- `source` (optional): Filter by source (`bluetooth_pbap`, `teams`, `placetel`, `manual`)

Response: `200 OK` with array of CallLog objects

Example:
```bash
curl "http://localhost:8000/calls?start=2025-11-01T00:00:00Z&end=2025-11-15T23:59:59Z&source=teams"
```

### 2. Get Call Log by ID

**GET** `/calls/{call_log_id}`

Response: `200 OK` with CallLog object, or `404 Not Found`

### 3. Create Call Log

**POST** `/calls`

Request body: CallLogCreate schema

Response: `201 Created` with CallLog object, or `409 Conflict` if duplicate

Example:
```json
{
  "user_id": "user123",
  "source": "manual",
  "external_id": "manual_2025-11-15_001",
  "started_at": "2025-11-15T10:00:00Z",
  "ended_at": "2025-11-15T10:15:00Z",
  "direction": "OUTBOUND",
  "remote_number": "+491234567890",
  "remote_name": "John Doe"
}
```

### 4. Sync Teams Calls

**POST** `/calls/sync/teams`

Query parameters (required):
- `start`: ISO8601 datetime
- `end`: ISO8601 datetime
- `user_id` (optional): User ID to associate with synced calls

Response: `200 OK` with sync status, or `501 Not Implemented` if Teams integration not configured

Example:
```bash
curl -X POST "http://localhost:8000/calls/sync/teams?start=2025-11-15T00:00:00Z&end=2025-11-15T23:59:59Z&user_id=user123"
```

**Note**: Requires Teams credentials to be configured in settings (see Configuration section below).

### 5. Placetel Webhook

**POST** `/calls/webhooks/placetel`

Webhook endpoint for Placetel real-time call events.

Headers:
- `X-Placetel-Signature` (optional): HMAC signature for verification

Request body: Placetel webhook payload (JSON)

Response: `200 OK` with call log ID, or `403 Forbidden` if signature invalid

Example payload:
```json
{
  "event": "CallCreated",
  "call_id": "abc123",
  "type": "inbound",
  "from": "+491234567890",
  "from_name": "John Doe",
  "to": "+490987654321",
  "timestamp": "2025-11-15T10:00:00Z"
}
```

## Integrations

### Microsoft Teams ([integrations/teams.py](backend/app/integrations/teams.py))

**Authentication**: App-Only (MSAL client credentials flow)

**Required credentials** (in settings):
- `teams_tenant_id` - Azure AD tenant ID
- `teams_client_id` - App registration client ID
- `teams_client_secret` - App registration client secret

**API**: Microsoft Graph Call Records API
- Endpoint: `GET https://graph.microsoft.com/v1.0/communications/callRecords`
- Scopes: `CallRecords.Read.All`

**Status**: ⚠️ **TODO - Not fully implemented**
- Token acquisition function needs MSAL library: `pip install msal`
- Graph API call function needs HTTP client: `pip install httpx` or `pip install aiohttp`

**Functions**:
- `sync_teams_calls_for_timerange(db, start, end, user_id)` - Main sync function
- `map_teams_callrecord_to_calllogs(record, user_id)` - Maps Graph API records to CallLog

### Placetel ([integrations/placetel.py](backend/app/integrations/placetel.py))

**Authentication**: Webhook signature (HMAC-SHA256)

**Required credentials** (in settings):
- `placetel_shared_secret` - Shared secret for webhook signature validation

**Webhook events**:
- `CallCreated` / `Ringing` - Call initiated
- `CallAnswered` / `Connected` - Call answered
- `CallHungup` / `Hangup` - Call ended

**Status**: ⚠️ **TODO - Signature verification not implemented**
- Currently accepts all webhooks (insecure for production)
- Implement HMAC signature check in `verify_placetel_signature()`

**Functions**:
- `apply_placetel_event_to_calllog(db, payload)` - Process webhook event and upsert CallLog
- `verify_placetel_signature(payload, signature)` - Verify webhook authenticity

### Bluetooth/PBAP ([migrations.py](backend/app/migrations.py))

**Status**: ✅ **Implemented**

Existing phone events from the `Event` table are automatically migrated to `CallLog` on first startup.

**Migration**:
- Runs automatically in `database.py::init_db()` → `_run_data_migrations()`
- Migrates all phone events with `source_type=PHONE`
- Maps to `source=BLUETOOTH_PBAP`
- Uses `external_id=bluetooth_event_{event.id}` for deduplication
- Preserves original data in `raw_payload`

**Direction mapping**:
- `INCOMING` → `INBOUND`
- `OUTGOING` → `OUTBOUND`
- `MISSED` → `INBOUND` (with note in raw_payload)

## Configuration

All integration credentials are stored in `backend/logging_settings.json` via the settings pattern.

### Settings Structure

```json
{
  "privacy_mode_until": null,
  "whitelist": [],
  "blacklist": [],
  "bluetooth_enabled": true,

  // Teams credentials
  "teams_tenant_id": null,
  "teams_client_id": null,
  "teams_client_secret": null,

  // Placetel credentials
  "placetel_shared_secret": null
}
```

### Setting Credentials

**Via API** (using existing settings endpoints):
```bash
# Load current settings
curl http://localhost:8000/settings

# Update settings (example - adjust endpoint as needed)
# TODO: Check if settings.py router supports direct key updates
```

**Via file** (manual edit):
1. Edit `backend/logging_settings.json`
2. Add credentials to the JSON structure
3. Restart backend

**TODO items for production**:
- [ ] Add encrypted credential storage (e.g., using Fernet or similar)
- [ ] Add environment variable fallback for credentials
- [ ] Add credentials management UI in frontend
- [ ] Implement credential rotation support

## Service Layer

The service layer ([services.py](backend/app/services.py)) provides business logic functions:

### `get_calllogs_for_user_and_range(db, user_id, start, end, source)`

Retrieve call logs with filters. Used by the `/calls` GET endpoint.

### `upsert_calllog(db, source, external_id, ...)`

Create or update a CallLog based on source + external_id. Used for deduplication across integrations.

## Data Migration

### Automatic Migration on Startup

When the backend starts:
1. `database.py::init_db()` creates all tables
2. `_run_data_migrations()` is called
3. Checks if `CallLog` table is empty and `Event` table has phone events
4. If yes, runs `migrate_events_to_calllogs(db)` to copy data

### Manual Migration

You can also trigger migration manually or re-run as needed:

```python
from app.database import get_session
from app.migrations import migrate_events_to_calllogs

with get_session() as db:
    stats = migrate_events_to_calllogs(db, dry_run=False)
    print(stats)
    # Output: {'total_phone_events': 150, 'migrated': 150, 'skipped': 0, 'errors': 0}
```

**Dry run** (to check without migrating):
```python
stats = migrate_events_to_calllogs(db, dry_run=True)
```

## Future Enhancements

### Planned Features
- [ ] Add user mapping for Placetel (map Placetel user IDs to TimeTrack user_ids)
- [ ] Implement Teams user detection (determine if current user is organizer/participant)
- [ ] Add WebRTC/SIP integrations for additional call sources
- [ ] Add call recording links (if available from sources)
- [ ] Add call analytics endpoints (duration stats, call frequency, etc.)
- [ ] Add export functionality for call logs (CSV, Excel)
- [ ] Add filtering by phone number/contact name
- [ ] Add deduplication across sources (e.g., same call logged by Teams + Placetel)

### Frontend Integration
- [ ] Add CallLog view in frontend
- [ ] Add call source filter UI
- [ ] Add time range picker for call queries
- [ ] Add Teams sync trigger button
- [ ] Add credentials configuration UI
- [ ] Add call timeline visualization
- [ ] Add contact name resolution from multiple sources

## Troubleshooting

### Teams sync fails with "Not implemented"

**Cause**: MSAL library not installed or token acquisition not implemented.

**Fix**:
1. Install MSAL: `pip install msal`
2. Verify credentials are set in `backend/logging_settings.json`
3. Check Azure AD app registration has `CallRecords.Read.All` permission

### Placetel webhook signature verification fails

**Cause**: Shared secret mismatch or signature verification not implemented.

**Fix**:
1. Ensure `placetel_shared_secret` matches Placetel webhook configuration
2. Implement HMAC verification in `integrations/placetel.py::verify_placetel_signature()`
3. Check webhook payload format matches expected structure

### Migration doesn't run

**Cause**: CallLog table already has data or no phone events exist.

**Fix**:
1. Check `CallLog` table: `SELECT COUNT(*) FROM calllogs;`
2. Check `Event` table: `SELECT COUNT(*) FROM events WHERE source_type = 'phone';`
3. If needed, clear CallLog and restart: `DELETE FROM calllogs; [restart backend]`

### Duplicate call logs

**Cause**: `external_id` not unique or different sources creating separate entries.

**Fix**:
1. Check `source + external_id` combination for duplicates
2. Verify integration is using consistent external_id format
3. Implement cross-source deduplication if needed

## Testing

### Manual Testing

**1. Create a test call log**:
```bash
curl -X POST http://localhost:8000/calls \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "source": "manual",
    "external_id": "test_001",
    "started_at": "2025-11-15T10:00:00Z",
    "ended_at": "2025-11-15T10:05:00Z",
    "direction": "OUTBOUND",
    "remote_number": "+491234567890",
    "remote_name": "Test Contact"
  }'
```

**2. List all call logs**:
```bash
curl http://localhost:8000/calls
```

**3. Filter by time range**:
```bash
curl "http://localhost:8000/calls?start=2025-11-01T00:00:00Z&end=2025-11-30T23:59:59Z"
```

**4. Test Placetel webhook** (simulate incoming call):
```bash
curl -X POST http://localhost:8000/calls/webhooks/placetel \
  -H "Content-Type: application/json" \
  -d '{
    "event": "CallCreated",
    "call_id": "test_placetel_001",
    "type": "inbound",
    "from": "+491111111111",
    "from_name": "Incoming Caller",
    "to": "+492222222222",
    "timestamp": "2025-11-15T12:00:00Z"
  }'
```

### Automated Testing

TODO: Add pytest test cases for:
- CallLog model CRUD
- Integration mapping functions
- Router endpoints
- Migration logic
- Service layer functions

## API Documentation

FastAPI automatically generates API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Navigate to the "calls" tag to see all CallLog endpoints with interactive testing.

---

**Last Updated**: 2025-11-15
**Author**: TimeTrack Development Team
