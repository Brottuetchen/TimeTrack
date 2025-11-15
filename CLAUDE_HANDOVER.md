# TimeTrack - Claude Code Web Handover

## Projekt-Übersicht

**TimeTrack** ist ein vollständiges Time-Tracking-System bestehend aus:
- **Backend** (FastAPI + SQLAlchemy + SQLite)
- **Frontend** (React + TypeScript + Vite + TailwindCSS)
- **Windows Agent** (Python-Tray-App mit Auto-Tracking)
- **Deployment** (Docker Compose auf Raspberry Pi)

## Aktueller Stand (November 2025)

### ✅ Implementierte Features

#### 1. **Unified CallLog-System**
- Zentrales CallLog-Modell für alle Anrufquellen
- Unterstützte Quellen: Bluetooth/PBAP, Microsoft Teams, Placetel, Manual
- Enums: `CallSource`, `CallDirection` (INBOUND/OUTBOUND/INTERNAL)
- Automatische Migration bestehender Phone Events zu CallLog
- Service-Layer: `get_calllogs_for_user_and_range()`, `upsert_calllog()`

**Backend-Dateien:**
- `backend/app/models.py` - CallLog-Modell
- `backend/app/schemas.py` - CallLog-Schemas
- `backend/app/routers/calls.py` - API-Endpoints
- `backend/app/services.py` - Service-Layer
- `backend/app/migrations.py` - Auto-Migration
- `backend/app/integrations/teams.py` - Teams Graph API
- `backend/app/integrations/placetel.py` - Placetel Webhook

**API-Endpoints:**
```
GET    /calls                      - Liste mit Filtern
POST   /calls                      - Manuell erstellen
GET    /calls/{id}                 - Einzelner CallLog
POST   /calls/sync/teams           - Teams-Sync
POST   /calls/webhooks/placetel    - Placetel Webhook
```

#### 2. **Windows Agent Call-Sync**
- `windows_agent/call_sync.py` - CallSyncManager-Thread
- Automatischer Sync alle 15 min (konfigurierbar)
- Manueller Trigger via Tray-Menü
- Status-Tracking (letzter Sync, Fehler, nächster Sync)
- Credentials-Management (lokal + Backend-Sync)

**Config-Erweiterung:**
```json
{
  "call_sync_enabled": true,
  "call_sync_interval_minutes": 15,
  "teams_enabled": false,
  "teams_tenant_id": null,
  "teams_client_id": null,
  "teams_client_secret": null,
  "placetel_enabled": false,
  "placetel_api_key": null,
  "placetel_api_url": "https://api.placetel.de/v2"
}
```

#### 3. **Frontend: Burger Menu Navigation**
- Komponente: `frontend/src/components/Navigation.tsx`
- Burger Menu oben rechts
- Dropdown mit Pages: Home (Logs), Admin (Settings), Privacy (Privacy-Einstellungen)
- Dark Mode Toggle im Menü
- Backdrop-Overlay beim Öffnen

**Page-Struktur:**
```
Home     → Event-Log-Tabelle mit Filtern & Bulk-Assign
Admin    → Tab-basiert (Privacy & Filter, Bluetooth, Call-Sync, Daten-Import, Logo)
Privacy  → Privacy-Einstellungen mit Info-Boxen
```

#### 4. **Logo-Upload-Feature**
- `frontend/src/components/LogoSettings.tsx` - Upload-Komponente
- `backend/app/routers/settings.py` - Logo-Endpoints (GET/PUT/DELETE)
- SVG-Upload (max 500 KB)
- Live-Preview und Auto-Skalierung (max-h-12, max-w-120px)
- Logo wird links neben "TimeTrack Review" angezeigt
- Custom Event für Live-Update ohne Reload
- Validierung: `<svg` oder `<?xml` Start

**API-Endpoints:**
```
GET    /settings/logo    - Logo abrufen
PUT    /settings/logo    - Logo hochladen
DELETE /settings/logo    - Logo entfernen
```

#### 5. **Performance-Optimierungen (Raspberry Pi)**
- Events nur laden bei Home-Page-Besuch (nicht beim Start)
- `fetchAssignments()` mit Filter-Parametern (start/end/limit)
- Backend: Assignments-Endpoint mit Zeitfiltern
- ~90% weniger Daten-Transfer
- Toast nur bei manuellem Reload
- Optimierte SQL-Queries mit JOINs und LIMIT

**Technische Details:**
- `limit=500` für Events
- `limit=1000` (max) für Assignments
- Lazy-Loading bei Page-Switching
- Effiziente joinedload() für Relationen

#### 6. **Event-Tracking-System**
- **Event-Typen:** window, phone, bluetooth
- **Bluetooth PBAP:** Anruf-Tracking via Bluetooth-Gerät
- **Auto-Tracking:** Windows Agent trackt aktive Fenster & Prozesse
- **Filtering:** Whitelist/Blacklist für Prozesse
- **Privacy-Mode:** Temporäres/unbegrenztes Pausieren
- **Bulk-Assign:** Mehrere Events gleichzeitig zuweisen
- **Privacy-Flag:** Events als privat markieren

#### 7. **Projekt-Management**
- Projekte & Milestones
- CSV-Import für Stammdaten
- Assignment-Tracking (Projekt, Milestone, Aktivitätstyp, Kommentar)
- Aktivitätstypen: Planung, Baustelle, Dokumentation, Meeting, Fahrt, Telefon, PC

## 🎯 Geplante Features (Priorität)

### 1. **Windows Tray-App Modernisierung** 🔥 HÖCHSTE PRIORITÄT
**Ziel:** Vollwertige Windows-Tray-App mit WebUI-Feature-Parity

**Tasks:**
- [ ] Native GUI statt CLI-basiert (PyQt6 oder wxPython)
- [ ] Dashboard-View mit Tagesstatistiken
- [ ] Live-Preview der getracknten Events (letzte 10)
- [ ] Quick-Assign: Direktes Zuweisen aus Tray
- [ ] Privacy-Mode-Toggle direkt im Tray
- [ ] Settings-Dialog für Whitelist/Blacklist
- [ ] Call-Sync-Status-Anzeige
- [ ] Benachrichtigungen bei wichtigen Events
- [ ] System-Tray-Icon mit Status-Indikator
- [ ] Mini-Kalender für Zeitraumauswahl
- [ ] Offline-Mode mit lokaler Queue

**Technische Umsetzung:**
- PyQt6 für moderne GUI
- Tray-Icon mit Kontextmenü
- Separate Fenster für Dashboard/Settings
- Lokale SQLite-DB für Offline-Cache
- WebSocket für Live-Updates (optional)

**Dateien:**
- `windows_agent/gui/main_window.py` (neu)
- `windows_agent/gui/tray_controller.py` (neu)
- `windows_agent/gui/dashboard.py` (neu)
- `windows_agent/gui/settings_dialog.py` (neu)

### 2. **Bulk-Operations erweitern** 🔥 HOCH
**Ziel:** Privacy-Flag und weitere Bulk-Operationen

**Tasks:**
- [ ] Bulk Privacy-Marking (Privat/Standard)
- [ ] Bulk-Delete für Events
- [ ] Bulk-Unassign (Zuweisung entfernen)
- [ ] Bulk-Copy (Assignment von einem Event auf andere kopieren)
- [ ] Undo-Funktion für Bulk-Operations

**Backend:**
```python
# backend/app/routers/events.py
@router.patch("/events/bulk")
def bulk_update_events(payload: BulkEventUpdate, db: Session = Depends(get_db)):
    # event_ids, is_private, delete, unassign
    pass
```

**Frontend:**
```tsx
// frontend/src/components/BulkAssignBar.tsx
// Neue Buttons: "Als privat markieren", "Löschen", "Zuweisung entfernen"
```

### 3. **Stammdaten-Management** 🔥 HOCH
**Ziel:** Bidirektionaler Stammdaten-Austausch

**Tasks:**
- [ ] Projekt-Export als CSV
- [ ] Milestone-Export als CSV
- [ ] API-Endpoints für CRUD (POST/PUT/DELETE Projekte/Milestones)
- [ ] Frontend-UI für direktes Bearbeiten
- [ ] Validierung bei Import/Export
- [ ] Archivierung alter Projekte

**API-Endpoints:**
```
POST   /projects           - Projekt erstellen
PUT    /projects/{id}      - Projekt bearbeiten
DELETE /projects/{id}      - Projekt löschen (soft-delete)
GET    /export/projects    - CSV-Export
POST   /milestones         - Milestone erstellen
PUT    /milestones/{id}    - Milestone bearbeiten
DELETE /milestones/{id}    - Milestone löschen
```

**Frontend:**
- Neue Admin-Tab "Stammdaten"
- Tabellen-View mit Inline-Editing
- Drag & Drop CSV-Upload
- Export-Button

### 4. **Telefonbuch-Management** 🔥 HOCH
**Ziel:** Automatische Namensauflösung für Anrufer

**Tasks:**
- [ ] Telefonbuch-Modell (PhoneBook: name, number, company, tags)
- [ ] CSV-Upload für Telefonbücher
- [ ] Automatisches Matching: CallLog.remote_number → PhoneBook.name
- [ ] Fuzzy-Matching für internationale Nummern
- [ ] Mehrere Telefonbücher (privat/geschäftlich)
- [ ] Frontend-UI für Telefonbuch-Verwaltung

**Backend:**
```python
# backend/app/models.py
class PhoneBook(Base):
    __tablename__ = "phonebook"
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    number = Column(String(32), nullable=False, index=True)
    company = Column(String(256))
    tags = Column(JSON)
    user_id = Column(String(64), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**CSV-Format:**
```csv
name,number,company,tags
Max Mustermann,+49123456789,ACME GmbH,"kunde,wichtig"
```

**API-Endpoints:**
```
GET    /phonebook               - Liste
POST   /phonebook               - Eintrag erstellen
PUT    /phonebook/{id}          - Eintrag bearbeiten
DELETE /phonebook/{id}          - Eintrag löschen
POST   /phonebook/import        - CSV-Upload
GET    /phonebook/export        - CSV-Export
GET    /phonebook/lookup/{num}  - Name für Nummer
```

**Frontend:**
- Admin-Tab "Telefonbuch"
- Tabellen-View mit Suche
- CSV-Upload & Export
- Inline-Editing

### 5. **Dashboard & Analytics** 🔶 MITTEL
**Ziel:** Statistiken und Visualisierungen

**Tasks:**
- [ ] Dashboard-Page (neue Route)
- [ ] Charts (Zeit pro Projekt, Aktivitätsverteilung)
- [ ] Tages-/Wochen-/Monatsübersicht
- [ ] Top-Projekte nach Zeitaufwand
- [ ] Export als PDF-Report

**Libraries:**
- recharts oder Chart.js
- react-to-pdf für PDF-Export

### 6. **Weitere Performance-Optimierungen** 🔶 MITTEL
**Ziel:** Sub-Sekunden-Ladezeiten auf Raspberry Pi

**Tasks:**
- [ ] Virtual Scrolling für Event-Tabelle (react-window)
- [ ] Debounced Search/Filter
- [ ] Backend: Pagination statt LIMIT
- [ ] Backend: Caching für Stammdaten (Redis optional)
- [ ] Frontend: React.memo() für teure Komponenten
- [ ] Frontend: useMemo/useCallback optimieren
- [ ] SQL-Indizes überprüfen und erweitern

**Technisch:**
```tsx
// Virtual Scrolling
import { FixedSizeList } from 'react-window';

// Pagination
const [page, setPage] = useState(1);
const [totalPages, setTotalPages] = useState(1);
fetchEvents({ ...filters, page, limit: 50 });
```

## 📁 Projekt-Struktur

```
TimeTrack/
├── backend/
│   ├── app/
│   │   ├── routers/          # API-Endpoints
│   │   │   ├── events.py
│   │   │   ├── assignments.py
│   │   │   ├── calls.py      # ✨ Neu: CallLog-API
│   │   │   ├── settings.py   # Logo, Privacy, Logging
│   │   │   ├── bluetooth.py
│   │   │   └── ...
│   │   ├── integrations/     # ✨ Neu: Externe APIs
│   │   │   ├── teams.py      # Microsoft Graph
│   │   │   └── placetel.py   # Placetel Webhook
│   │   ├── models.py         # SQLAlchemy Models
│   │   ├── schemas.py        # Pydantic Schemas
│   │   ├── services.py       # ✨ Neu: Business Logic
│   │   ├── migrations.py     # ✨ Neu: Auto-Migrations
│   │   ├── database.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navigation.tsx       # ✨ Burger Menu
│   │   │   ├── AdminPage.tsx        # ✨ Tab-basiert
│   │   │   ├── PrivacyPage.tsx      # ✨ Neu
│   │   │   ├── LogoSettings.tsx     # ✨ Neu: SVG-Upload
│   │   │   ├── CallSyncSettings.tsx # ✨ Neu: Teams/Placetel
│   │   │   ├── EventsTable.tsx
│   │   │   ├── FiltersBar.tsx
│   │   │   └── ...
│   │   ├── App.tsx           # ✨ Page-Routing, Logo-Display
│   │   ├── api.ts            # ✨ Optimiert: Filter-Parameter
│   │   └── types.ts
│   ├── package.json
│   └── Dockerfile
├── windows_agent/
│   ├── main.py               # ✨ CallSyncManager integriert
│   ├── call_sync.py          # ✨ Neu: Call-Sync-Thread
│   ├── config.example.json   # ✨ Call-Sync-Config
│   └── ...
├── docker-compose.yml
└── CLAUDE_HANDOVER.md        # Diese Datei
```

## 🔧 Tech-Stack

### Backend
- **Framework:** FastAPI 0.100+
- **ORM:** SQLAlchemy 2.0
- **DB:** SQLite
- **Auth:** API-Key (optional für Windows Agent)
- **Integrations:** MSAL (Teams), httpx (HTTP-Requests)

### Frontend
- **Framework:** React 18 + TypeScript
- **Build:** Vite
- **Styling:** TailwindCSS
- **Router:** State-based (currentPage)
- **HTTP:** axios
- **Notifications:** react-hot-toast
- **Date:** dayjs

### Windows Agent
- **Runtime:** Python 3.11
- **Tray:** pystray (aktuell CLI-basiert)
- **Bluetooth:** pybluez
- **HTTP:** requests
- **Geplant:** PyQt6 für GUI

### Deployment
- **Platform:** Raspberry Pi (Low-Power)
- **Container:** Docker Compose
- **Proxy:** Nginx (Frontend)
- **Storage:** SQLite + Volumes

## 📊 Datenmodelle (Wichtigste)

### Event
```python
class Event(Base):
    id: int
    user_id: str
    timestamp: datetime
    source_type: SourceType  # window, phone, bluetooth
    process_name: str | None
    window_title: str | None
    contact_name: str | None
    phone_number: str | None
    duration_seconds: int | None
    is_private: bool = False  # Privacy-Flag
```

### CallLog ✨ NEU
```python
class CallLog(Base):
    id: int
    user_id: str | None
    source: CallSource  # BLUETOOTH_PBAP, TEAMS, PLACETEL, MANUAL
    external_id: str    # Dedupe-Key
    started_at: datetime
    ended_at: datetime | None
    direction: CallDirection | None  # INBOUND, OUTBOUND, INTERNAL
    remote_number: str | None
    remote_name: str | None
    raw_payload: dict | None
```

### Assignment
```python
class Assignment(Base):
    id: int
    event_id: int  # FK → Event
    project_id: int  # FK → Project
    milestone_id: int | None  # FK → Milestone
    activity_type: str | None  # Planung, Baustelle, ...
    comment: str | None
```

### Project
```python
class Project(Base):
    id: int
    name: str
    number: str  # Projektnummer
    description: str | None
```

### Milestone
```python
class Milestone(Base):
    id: int
    project_id: int  # FK → Project
    name: str
    number: str
    description: str | None
```

## 🚀 Development-Workflow

### Lokale Entwicklung
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev  # Port 5173

# Windows Agent (auf Windows)
cd windows_agent
pip install -r requirements.txt
python main.py
```

### Docker Deployment
```bash
# Build & Start
docker compose up -d --build

# Logs
docker compose logs -f api
docker compose logs -f web

# Stop
docker compose down
```

### Git-Workflow
```bash
git add .
git commit -m "feat: Beschreibung"
git push origin master
```

## 🔑 Wichtige Konfigurationen

### Backend Settings (logging_settings.json)
```json
{
  "whitelist": ["acad.exe", "code.exe"],
  "blacklist": ["chrome.exe"],
  "bluetooth_enabled": true,
  "privacy_mode_until": null,
  "teams_tenant_id": "...",
  "teams_client_id": "...",
  "teams_client_secret": "...",
  "placetel_shared_secret": "...",
  "logo_svg": "<svg>...</svg>"
}
```

### Windows Agent Config
```json
{
  "backend_url": "http://localhost:8000",
  "user_id": "user123",
  "poll_interval_seconds": 5,
  "buffer_file": "%APPDATA%/TimeTrack/buffer.json",
  "call_sync_enabled": true,
  "call_sync_interval_minutes": 15,
  "teams_enabled": false,
  "placetel_enabled": false
}
```

## 🐛 Bekannte Issues

1. **Logo-Upload:** ✅ GELÖST - Validierung akzeptiert jetzt `<?xml` Deklaration
2. **Performance:** ✅ VERBESSERT - Assignments mit Zeitfiltern, lazy loading
3. **Windows Agent GUI:** ❌ NOCH CLI - Modernisierung geplant (siehe Features)

## 📝 Coding-Standards

### Backend
- Type Hints für alle Funktionen
- Pydantic für Validierung
- Docstrings für komplexe Logik
- HTTPException für Fehler (status_code + detail)
- Dependency Injection (`Depends(get_db)`)

### Frontend
- TypeScript strict mode
- Functional Components + Hooks
- Props-Interfaces für alle Komponenten
- Error Handling mit try/catch + toast
- Dark Mode Support (Tailwind dark:)

### Naming
- Backend: snake_case
- Frontend: camelCase
- Komponenten: PascalCase
- Constants: UPPER_SNAKE_CASE

## 🎨 UI/UX-Guidelines

- **Farben:** Blue (primary), Slate (grays), Red (errors), Green (success)
- **Dark Mode:** Alle Komponenten müssen dark: Varianten haben
- **Responsive:** Mobile-first (Tailwind breakpoints)
- **Accessibility:** aria-labels für Buttons
- **Loading States:** Spinner + "Lädt..." Text
- **Toasts:** Erfolg (grün), Fehler (rot), Info (blau)

## 🔒 Security Notes

- **API-Key:** Optional für Windows Agent (Production)
- **HTTPS:** Cloudflare Tunnel in Production
- **Secrets:** Nie in Git committen (logging_settings.json in .gitignore)
- **SQL-Injection:** Geschützt durch SQLAlchemy ORM
- **XSS:** React escaped automatisch, ABER `dangerouslySetInnerHTML` bei Logo (akzeptabel, da Admin-Upload)

## 📚 Wichtige Dokumentation

- **FastAPI Docs:** http://localhost:8000/docs (Swagger UI)
- **Backend CALLLOG_INTEGRATION.md:** Vollständige CallLog-Doku
- **Windows Agent CALLSYNC_INTEGRATION.md:** Call-Sync-Guide
- **Frontend:** Komponenten-Kommentare inline

## 🎯 Next Steps für Claude Code Web

1. **Tray-App modernisieren** - PyQt6 GUI implementieren
2. **Bulk-Privacy** - Frontend + Backend erweitern
3. **Stammdaten-CRUD** - Volle CRUD-API + UI
4. **Telefonbuch** - Neues Modell + CSV-Import
5. **Virtual Scrolling** - Performance für große Tabellen

## 💡 Tipps für Claude Code Web

- **Performance:** Raspberry Pi ist Low-Power → LIMIT, Filter, Pagination
- **Testing:** Lokaler Dev-Server besser als Docker für schnelle Iteration
- **Git:** Kleine, atomare Commits bevorzugt
- **UI:** Konsistenz mit bestehenden Komponenten (z.B. AdminPage-Tabs)
- **Dark Mode:** Immer testen (Toogle oben rechts im Burger Menu)

---

**Letzte Aktualisierung:** 2025-11-15
**Status:** ✅ Produktiv, Performance optimiert, Logo-Upload funktioniert
**Git Branch:** master
**Deployment:** Raspberry Pi @ http://192.168.188.145
