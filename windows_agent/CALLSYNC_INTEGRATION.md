# Windows Agent - Call-Sync Integration

## Übersicht

Der Windows Agent wurde erweitert um eine **Call-Sync-Funktion**, die automatisch Anrufe aus Microsoft Teams und Placetel synchronisiert. Die Synchronisation läuft als Hintergrund-Thread parallel zum normalen Window-Tracking.

## Features

- ✅ **Automatische Synchronisation** alle 15 Minuten (konfigurierbar)
- ✅ **Microsoft Teams** via Graph API Call Records
- ✅ **Placetel** via Webhook (empfängt Events in Echtzeit)
- ✅ **Manueller Sync** über Tray-Menü
- ✅ **Status-Anzeige** im Tray-Menü (letzter Sync, Fehler, nächster Sync)
- ✅ **Web-UI** zur Konfiguration im Frontend

## Architektur

```
┌─────────────────────────┐
│   Windows Agent         │
│   (main.py)             │
│                         │
│  ┌──────────────────┐   │
│  │ WindowTracker    │   │  (bestehendes Feature)
│  └──────────────────┘   │
│                         │
│  ┌──────────────────┐   │
│  │ EventSender      │   │  (bestehendes Feature)
│  └──────────────────┘   │
│                         │
│  ┌──────────────────┐   │
│  │ CallSyncManager  │◄─────┐ NEU!
│  └──────────────────┘   │  │
│         │               │  │
│         │ HTTP POST     │  │
│         ▼               │  │
│  ┌──────────────────┐   │  │
│  │ FastAPI Backend  │   │  │
│  │ /calls/sync/teams│   │  │
│  └──────────────────┘   │  │
│         │               │  │
│         ▼               │  │
│  ┌──────────────────┐   │  │
│  │ Teams Graph API  │   │  │
│  │ CallRecords      │   │  │
│  └──────────────────┘   │  │
└─────────────────────────┘  │
                             │
                             │
┌─────────────────────────┐  │
│   Frontend (React)      │  │
│                         │  │
│  ┌──────────────────┐   │  │
│  │ CallSyncSettings │◄──┘
│  │ Component        │   │
│  └──────────────────┘   │
│                         │
│  - Teams Credentials    │
│  - Placetel Secret      │
│  - Manueller Sync       │
└─────────────────────────┘
```

## Konfiguration

### 1. Windows Agent Config (`config.json`)

```json
{
  "base_url": "http://localhost:8000",
  "machine_id": "pc-lars",
  "user_id": "lars",

  "call_sync_enabled": true,
  "call_sync_interval_minutes": 15,

  "teams_enabled": true,
  "teams_tenant_id": "00000000-0000-0000-0000-000000000000",
  "teams_client_id": "00000000-0000-0000-0000-000000000000",
  "teams_client_secret": "your-client-secret-here",

  "placetel_enabled": false,
  "placetel_api_key": null,
  "placetel_api_url": "https://api.placetel.de/v2"
}
```

**Parameter**:
- `call_sync_enabled` - Aktiviert/deaktiviert den Call-Sync (default: false)
- `call_sync_interval_minutes` - Sync-Intervall in Minuten (default: 15)
- `teams_enabled` - Aktiviert Teams-Synchronisation
- `teams_tenant_id` - Azure AD Tenant ID
- `teams_client_id` - Azure AD App Registration Client ID
- `teams_client_secret` - Azure AD App Registration Client Secret
- `placetel_enabled` - Aktiviert Placetel (für zukünftige Erweiterung)

### 2. Azure AD App Registration (für Teams)

1. **Azure Portal** → **Azure Active Directory** → **App registrations** → **New registration**
2. Name: `TimeTrack Call Sync`
3. Supported account types: **Single tenant**
4. Redirect URI: **nicht erforderlich** (App-Only Auth)
5. **API permissions** → **Add permission** → **Microsoft Graph** → **Application permissions**
   - `CallRecords.Read.All` ✓
6. **Grant admin consent** für die Permissions
7. **Certificates & secrets** → **New client secret** → Kopiere den Secret
8. **Overview** → Kopiere **Application (client) ID** und **Directory (tenant) ID**

### 3. Backend Settings

Die Credentials werden beim Start des Call-Sync-Managers automatisch ins Backend geschrieben (`backend/logging_settings.json`):

```json
{
  "teams_tenant_id": "...",
  "teams_client_id": "...",
  "teams_client_secret": "...",
  "placetel_shared_secret": null
}
```

Alternativ können die Settings auch über die **Web-UI** (Frontend) oder direkt über die **API** gesetzt werden:

```bash
curl -X PUT http://localhost:8000/api/settings/logging \
  -H "Content-Type: application/json" \
  -d '{
    "teams_tenant_id": "...",
    "teams_client_id": "...",
    "teams_client_secret": "..."
  }'
```

## Verwendung

### Windows Agent starten

```bash
cd windows_agent
python main.py
```

Der Agent startet automatisch:
1. WindowTracker (bestehend)
2. EventSender (bestehend)
3. CallSyncManager (neu) - wenn `call_sync_enabled: true`

### Tray-Menü

Rechtsklick auf Tray-Icon:
- **Tracking aktiv** - An/Aus
- **Offene Events senden** - Manuell
- **Status anzeigen** - Zeigt Status inkl. Call-Sync Info
- **Call-Sync jetzt ausführen** ⭐ **NEU** - Triggert manuellen Sync
- **Config öffnen**
- **Logdatei öffnen**
- **Beenden**

### Status-Fenster

Beispiel-Output:

```
Tracking aktiv
Offene Events: 5
Letzter Upload: 15.11.2025 14:30
Letzter Fehler: –
Privacy-Modus: inaktiv

Call-Sync: ✓ (alle 15 min)
Letzter Sync: 15.11.2025 14:25
Nächster Sync in: 10 min
```

Bei Fehler:

```
Call-Sync: ✗ (alle 15 min)
Letzter Sync: 15.11.2025 14:25
Nächster Sync in: 10 min
Fehler: Teams-Integration noch nicht vollständig im...
```

### Web-UI Konfiguration

1. **Frontend öffnen**: http://localhost:3000
2. Scroll runter zur **Call-Sync Einstellungen** Sektion
3. **Microsoft Teams** Sektion:
   - Tenant ID eingeben
   - Client ID eingeben
   - Client Secret eingeben (wird maskiert)
   - **"Einstellungen speichern"** klicken
4. **Teams-Sync manuell starten** Button testet die Konfiguration (synchronisiert letzte 7 Tage)

## Implementierung

### CallSyncManager (`call_sync.py`)

Neuer Daemon-Thread der:
1. Alle X Minuten einen Sync durchführt
2. Teams-Credentials ins Backend schreibt
3. Backend-Endpoint `/calls/sync/teams` aufruft
4. Status tracked (last_sync_time, last_sync_success, last_sync_error, sync_count)
5. Manuellen Trigger unterstützt

**Wichtige Methoden**:
- `run()` - Haupt-Loop mit Intervall-Handling
- `trigger_manual_sync()` - Manueller Trigger
- `get_status()` - Status-Dict für Tray-Anzeige
- `_sync_teams_calls()` - Ruft Backend-API auf
- `_update_backend_settings()` - Schreibt Credentials ins Backend

### Integration in main.py

```python
# CallSyncManager starten wenn aktiviert
call_sync_manager = None
if cfg.call_sync_enabled and (cfg.teams_enabled or cfg.placetel_enabled):
    logger.info("Starte CallSyncManager...")
    call_sync_manager = CallSyncManager(
        base_url=cfg.base_url,
        user_id=cfg.user_id,
        logger=logger,
        sync_interval_minutes=cfg.call_sync_interval_minutes,
        teams_enabled=cfg.teams_enabled,
        teams_tenant_id=cfg.teams_tenant_id,
        teams_client_id=cfg.teams_client_id,
        teams_client_secret=cfg.teams_client_secret,
        ...
    )
    call_sync_manager.start()
```

### TrayController Erweiterungen

- **Konstruktor**: Akzeptiert `call_sync_manager: Optional[CallSyncManager]`
- **Menü**: Fügt "Call-Sync jetzt ausführen" hinzu wenn Manager aktiv
- **status_text()**: Erweitert um Call-Sync Status (letzter Sync, Fehler, nächster Sync)
- **trigger_call_sync()**: Triggert manuellen Sync
- **quit()**: Stoppt Call-Sync-Manager gracefully

### Frontend-Komponente (`CallSyncSettings.tsx`)

React-Komponente mit:
- **Teams-Settings** - Tenant ID, Client ID, Client Secret (maskiert)
- **Placetel-Settings** - Shared Secret + Webhook-URL Anzeige
- **Status-Anzeige** - Letzter Sync, Erfolg/Fehler, Anzahl Syncs, nächster Sync
- **Manueller Trigger** - Button zum Testen der Teams-Integration (letzte 7 Tage)
- **Speichern-Button** - Schreibt Settings via PUT `/api/settings/logging`

### Backend-Erweiterungen

#### Settings Router (`routers/settings.py`)

- **LoggingSettingsUpdate Schema** erweitert um:
  - `teams_tenant_id`
  - `teams_client_id`
  - `teams_client_secret`
  - `placetel_shared_secret`
- **PUT /logging** - Speichert Call-Sync-Settings
- **POST /logging** - Alternative für Windows Agent (merged vollständiges Dict)

#### Calls Router (`routers/calls.py`)

Bereits vorhanden aus vorheriger CallLog-Integration:
- **POST /calls/sync/teams** - Endpoint den der CallSyncManager aufruft
- **POST /calls/webhooks/placetel** - Webhook für Placetel

## Ablauf eines Syncs

1. **CallSyncManager** wartet bis Intervall erreicht (oder manueller Trigger)
2. Ruft `_sync_teams_calls()` auf
3. Berechnet Zeitfenster:
   - `start` = last_sync_time (oder now - 24h beim ersten Mal)
   - `end` = now
4. HTTP POST zu `{base_url}/calls/sync/teams?start=...&end=...&user_id=...`
5. **Backend** (`integrations/teams.py`):
   - Lädt Credentials aus Settings
   - Authentifiziert via MSAL (TODO: needs msal library)
   - Ruft Graph API auf (TODO: needs httpx library)
   - Mapped Call Records → CallLog
   - Upsert in DB (basierend auf external_id)
6. **CallSyncManager** erhält Response:
   - `200 OK` → `last_sync_success = True, last_sync_error = None`
   - `501 Not Implemented` → Teams-Integration noch nicht fertig (msal fehlt)
   - `400/500` → `last_sync_success = False, last_sync_error = error message`
7. Status wird upgedatet, nächster Sync in X Minuten

## Logging

Alle Call-Sync-Aktivitäten werden im Windows Agent Log protokolliert:

```
%APPDATA%/TimeTrack/timetrack_agent.log
```

Beispiel-Log:

```
2025-11-15 14:25:00 [INFO] CallSyncManager gestartet (Intervall: 15 min, Teams: True, Placetel: False)
2025-11-15 14:25:10 [INFO] Teams-Credentials erfolgreich ins Backend geschrieben
2025-11-15 14:25:10 [INFO] Starte Call-Synchronisation...
2025-11-15 14:25:10 [INFO] Starte Teams-Sync: 2025-11-14T14:25:10 bis 2025-11-15T14:25:10
2025-11-15 14:25:15 [INFO] Teams-Sync erfolgreich: {'status': 'success', 'message': '...'}
2025-11-15 14:25:15 [INFO] Call-Sync abgeschlossen (#1)
```

Bei Fehler:

```
2025-11-15 14:25:15 [WARNING] Teams-Integration noch nicht vollständig implementiert (msal/httpx fehlt)
```

## Troubleshooting

### Call-Sync startet nicht

**Problem**: CallSyncManager wird nicht gestartet

**Lösung**:
1. Prüfe `config.json`: `call_sync_enabled: true`?
2. Prüfe `teams_enabled: true` oder `placetel_enabled: true`?
3. Check Log: `%APPDATA%/TimeTrack/timetrack_agent.log`

### Teams-Sync schlägt fehl mit "Not Implemented"

**Problem**: Backend gibt HTTP 501 zurück

**Ursache**: MSAL/httpx Libraries fehlen

**Lösung**:
```bash
cd backend
pip install msal httpx
```

Dann in `integrations/teams.py` die TODO-Marker implementieren.

### Credentials werden nicht gespeichert

**Problem**: Settings verschwinden nach Neustart

**Lösung**:
1. Prüfe ob `backend/logging_settings.json` existiert und writeable ist
2. Prüfe Backend-Log auf Fehler beim Speichern
3. Setze Credentials über Web-UI statt config.json

### Manueller Sync funktioniert nicht im Frontend

**Problem**: Button "Teams-Sync manuell starten" tut nichts

**Lösung**:
1. Öffne Browser Console (F12) - schaue nach Fehlern
2. Prüfe ob Backend erreichbar ist: `curl http://localhost:8000/api/health`
3. Prüfe Backend-Log auf Fehler
4. Stelle sicher dass Credentials korrekt gespeichert sind

### Tray-Menü zeigt keinen Call-Sync-Eintrag

**Problem**: "Call-Sync jetzt ausführen" fehlt im Menü

**Lösung**:
- CallSyncManager muss gestartet worden sein (check Log)
- Config muss `call_sync_enabled: true` haben
- Windows Agent neu starten

## Zukünftige Erweiterungen

### Geplant

- [ ] **Placetel Pull-API** - Falls Placetel ein Call-History-API hat (zusätzlich zu Webhooks)
- [ ] **Status-Endpoint** - Backend-Endpoint für Call-Sync-Status (für Frontend)
- [ ] **User-Mapping** - Map Placetel/Teams User IDs zu TimeTrack user_ids
- [ ] **Call-Deduplication** - Erkennung wenn gleicher Call von Teams + Placetel kommt
- [ ] **Selective Sync** - Nur bestimmte User/Gruppen synchronisieren
- [ ] **Sync-Historie** - Log aller Syncs mit Details (wann, wie viele Calls, Fehler)
- [ ] **Retry-Logic** - Bei temporären Netzwerkfehlern automatisch wiederholen
- [ ] **Notification** - Windows Toast bei erfolgreicher Sync

### Ideen

- **Andere Quellen**: Cisco Webex, Zoom, Slack Calls, etc.
- **Bidirektionale Sync**: CallLog zurück zu Teams schreiben (z.B. für Notes)
- **Analytics**: Dashboard mit Call-Statistiken (Anzahl, Dauer, Verteilung)

## Testing

### Manueller Test

1. **Config erstellen**:
   ```json
   {
     "call_sync_enabled": true,
     "teams_enabled": true,
     "teams_tenant_id": "<YOUR_TENANT_ID>",
     "teams_client_id": "<YOUR_CLIENT_ID>",
     "teams_client_secret": "<YOUR_CLIENT_SECRET>"
   }
   ```

2. **Windows Agent starten**:
   ```bash
   python main.py
   ```

3. **Log beobachten**:
   ```bash
   tail -f %APPDATA%\TimeTrack\timetrack_agent.log
   ```

4. **Manuellen Sync triggern**:
   - Rechtsklick auf Tray-Icon
   - "Call-Sync jetzt ausführen"

5. **Status prüfen**:
   - "Status anzeigen" im Tray-Menü
   - Sollte Call-Sync Info zeigen

6. **Backend-DB prüfen**:
   ```bash
   sqlite3 backend/timetrack.db
   SELECT * FROM calllogs WHERE source = 'teams';
   ```

### Unit Tests

TODO: Pytest-Tests erstellen für:
- `CallSyncManager._sync_teams_calls()`
- `CallSyncManager.get_status()`
- Integration mit TrayController

## Dependencies

Keine zusätzlichen Dependencies für den Windows Agent erforderlich - nutzt bereits vorhandene `requests` Library.

Backend-Dependencies (optional, für vollständige Teams-Integration):
```
msal>=1.20.0        # Microsoft Authentication Library
httpx>=0.24.0       # Async HTTP client für Graph API
```

---

**Last Updated**: 2025-11-15
**Author**: TimeTrack Development Team
