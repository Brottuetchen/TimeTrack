# Smart Event Aggregation - Implementation Guide

## Überblick

Dieses Feature implementiert ein 100% lokales Event-Aggregations-System für TimeTrack. Alle Operationen laufen auf dem Raspberry Pi - keine Cloud-Services, keine externen APIs.

## Was wurde implementiert?

### Backend (Python/FastAPI)

#### 1. Datenbank-Modelle (`backend/app/models.py`)
- **Session**: Aggregierte Event-Sessions mit Metadaten
  - Zeitspanne, Prozessname, Fenstertitel
  - Event-Zählung, Pausen-Zählung
  - Assignment-Verknüpfung

- **AssignmentRule**: Automatische Zuweisungs-Regeln
  - Pattern-Matching (Prozess, Titel)
  - Auto-Assignment zu Projekt/Milestone
  - Prioritäts-System

#### 2. Services (100% Lokal)

**`backend/app/services/session_aggregator.py`**
- SessionAggregator: Aggregiert Events zu Sessions
- Algorithmus:
  1. Sortiert Events nach Zeit
  2. Gruppiert nach Prozess + ähnlichem Titel
  3. Merged Events wenn Pause <5 Minuten
  4. Fuzzy-Matching via Python `difflib.SequenceMatcher` (kein API-Call!)
  5. Titel-Normalisierung mit Regex (lokal)

**`backend/app/services/assignment_rules.py`**
- RulesEngine: Wendet Regeln auf Events/Sessions an
- Matching-Engine: Komplett lokal (Regex, String-Matching)
- Keine KI, keine externen Services

#### 3. API-Endpoints

**`backend/app/routers/sessions.py`**
- `POST /sessions/aggregate` - Triggert Aggregation (lokal)
- `GET /sessions` - Listet Sessions
- `GET /sessions/{id}` - Einzelne Session
- `POST /sessions/{id}/assign` - Weist Session zu Projekt zu

**`backend/app/routers/rules.py`**
- `GET /rules` - Listet Assignment-Regeln
- `POST /rules` - Erstellt neue Regel
- `PUT /rules/{id}` - Aktualisiert Regel
- `DELETE /rules/{id}` - Löscht Regel

#### 4. Pydantic-Schemas (`backend/app/schemas.py`)
- SessionBase, SessionRead
- SessionAssignmentCreate
- AssignmentRuleBase, AssignmentRuleCreate, AssignmentRuleUpdate, AssignmentRuleRead

### Frontend (React/TypeScript)

#### 1. Types (`frontend/src/types.ts`)
- Session-Interface
- AssignmentRule-Interface
- SessionAssignmentPayload

#### 2. API (`frontend/src/api.ts`)
- `fetchSessions()` - Lädt Sessions
- `triggerAggregation()` - Triggert Aggregation
- `assignSession()` - Weist Session zu
- `fetchRules()`, `createRule()`, `updateRule()`, `deleteRule()` - Rules-Management

#### 3. Komponenten

**`frontend/src/components/SessionsView.tsx`**
- Zeigt aggregierte Sessions an
- Trigger-Button für Re-Aggregation
- Projekt-Zuweisung per Dropdown
- Statistiken (Sessions, Events, Aktive Zeit)

**`frontend/src/components/RulesManager.tsx`**
- CRUD für Assignment-Regeln
- Pattern-Editor (Prozess, Titel)
- Auto-Projekt/Milestone-Auswahl
- Prioritäts-Management
- Enable/Disable Toggle

### Migration

**`scripts/migrate_events_to_sessions.py`**
- Migriert bestehende Events zu Sessions
- Unterstützt Single-User und All-Users-Modus
- Konfigurierbarer Zeitraum (default: 30 Tage)

```bash
# Alle User migrieren (letzte 30 Tage)
python scripts/migrate_events_to_sessions.py

# Einzelner User
python scripts/migrate_events_to_sessions.py --user lars --days 60
```

## Datenschutz-Garantie ✅

Alle Komponenten laufen 100% lokal:

- ✅ **Session-Aggregation**: Python `difflib` (Standard-Library, kein Network)
- ✅ **Titel-Normalisierung**: Regex (lokal)
- ✅ **Rules-Engine**: String-Matching (lokal)
- ✅ **Fuzzy-Matching**: `SequenceMatcher` (Python Standard, kein API-Call)
- ✅ **Speicherung**: SQLite auf Pi (nicht in Cloud)

Keine externen Abhängigkeiten:
- ❌ Kein OpenAI / GPT
- ❌ Kein Google / Microsoft AI
- ❌ Keine Cloud-Services
- ❌ Keine Telemetrie

## Verwendung

### 1. Backend starten

```bash
cd ~/TimeTrack
docker compose up -d --build
```

### 2. Sessions aggregieren

```bash
# Via API
curl -X POST "http://localhost:8000/sessions/aggregate?user_id=lars"

# Via Migration-Script
python scripts/migrate_events_to_sessions.py --user lars
```

### 3. Sessions abrufen

```bash
curl "http://localhost:8000/sessions?user_id=lars&limit=10"
```

### 4. Frontend nutzen

Die SessionsView und RulesManager Komponenten können in die bestehende Frontend-App integriert werden.

## Erwartetes Ergebnis

**Vorher:**
- User sieht 200 Events (unübersichtlich)
- Muss jedes Event einzeln zuweisen (2h Arbeit)
- System wird nicht genutzt ❌

**Nachher:**
- User sieht 18 Sessions (übersichtlich)
- Weist Sessions zu: "acad.exe Projekt-X → 2.5h" (5min Arbeit)
- Optional: Erstellt Regel → zukünftig automatisch ✅
- System wird täglich genutzt ✅

## Konfiguration

### SessionAggregator-Parameter

```python
SessionAggregator(
    max_break_minutes=5,        # Max Pause zwischen Events
    min_title_similarity=0.65,  # Min Titel-Ähnlichkeit (0-1)
    min_session_duration_seconds=120  # Min Session-Dauer
)
```

### Assignment-Rule Beispiel

```python
{
    "name": "AutoCAD Projekt-X",
    "process_pattern": "acad.exe",
    "title_contains": "Projekt-X",
    "auto_project_id": 5,
    "auto_milestone_id": 12,
    "auto_activity": "CAD-Arbeit",
    "auto_comment_template": "Arbeit an {title}",
    "priority": 10
}
```

## Technische Details

### Session-Aggregation Algorithmus

1. **Event-Sortierung**: Nach `timestamp_start`
2. **Gruppierung**: Gleicher Prozess + ähnlicher Titel
3. **Fuzzy-Matching**:
   - Titel-Normalisierung (entfernt Programmnamen, Versionsnummern)
   - Similarity-Check via `SequenceMatcher.ratio()`
   - Threshold: 0.65 (65% Ähnlichkeit)
4. **Zeit-Lücken**: Merge wenn Pause <5 Minuten
5. **Break-Counting**: Pausen >1 Minute werden gezählt

### Rules-Engine Matching

1. **Prozess-Pattern**: Wildcard-Matching (`*` = beliebig viele Zeichen)
2. **Titel-Contains**: Case-insensitive Substring-Check
3. **Titel-Regex**: Optionale Regex für komplexe Matches
4. **Priorität**: Regeln werden nach Priorität (DESC) abgearbeitet
5. **First-Match**: Erste passende Regel gewinnt

## Troubleshooting

### Sessions werden nicht erstellt
- Check: Sind Events vorhanden? (`GET /events`)
- Check: Sind Events vom Typ `window`?
- Check: Haben Events `timestamp_end` gesetzt?
- Check: Ist `duration_seconds` >= 10?

### Regeln greifen nicht
- Check: Ist Regel `enabled=true`?
- Check: Pattern matcht? (Test mit `process_pattern="*"`)
- Check: Projekt/Milestone existieren?
- Check: Priorität korrekt? (höhere Zahl = höhere Prio)

### Performance
- Session-Aggregation ist sehr schnell (100-200 Events in <1s)
- Fuzzy-Matching via `difflib` ist effizient (C-optimiert)
- Keine API-Calls = keine Network-Latenz

## Nächste Schritte

1. **Frontend-Integration**: SessionsView in Navigation einbinden
2. **Auto-Aggregation**: Cronjob für tägliche Aggregation
3. **Analytics**: Dashboard mit Session-Statistiken
4. **Export**: CSV-Export für Sessions
5. **Mobile-App**: Session-View für Mobile

## Support

Bei Fragen oder Problemen:
- Check Logs: `docker compose logs backend`
- Test Endpoints: `curl http://localhost:8000/docs`
- Migration-Script: `python scripts/migrate_events_to_sessions.py --help`
