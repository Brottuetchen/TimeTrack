# Claude Code Web - TimeTrack Entwicklungs-Prompt

Du arbeitest am **TimeTrack**-Projekt (Nov 2025), einem vollständigen Time-Tracking-System mit FastAPI-Backend, React-Frontend und Windows-Agent.

## 📖 Kontext laden

Lies **ZUERST** diese Dateien:
1. `CLAUDE_HANDOVER.md` - Vollständige Projekt-Dokumentation
2. `backend/CALLLOG_INTEGRATION.md` - CallLog-System-Doku
3. `windows_agent/CALLSYNC_INTEGRATION.md` - Windows Agent Call-Sync

## 🎯 Aktuelle Prioritäten

### 1. Windows Tray-App Modernisierung (HÖCHSTE PRIORITÄT)
**Ziel:** Vollwertige GUI-App statt CLI

**Was zu tun ist:**
- Ersetze CLI-basierte Tray-App durch PyQt6-GUI
- Implementiere Dashboard mit Live-Event-Preview
- Quick-Assign-Funktion direkt aus Tray
- Privacy-Mode-Toggle
- Settings-Dialog für Whitelist/Blacklist
- Call-Sync-Status-Anzeige

**Dateien erstellen:**
- `windows_agent/gui/main_window.py`
- `windows_agent/gui/tray_controller.py`
- `windows_agent/gui/dashboard.py`
- `windows_agent/gui/settings_dialog.py`

**Dependencies:**
```bash
pip install PyQt6 PyQt6-tools
```

### 2. Bulk-Operations erweitern
**Ziel:** Privacy-Flag Bulk-Marking

**Backend:**
- Erstelle `PATCH /events/bulk` Endpoint
- Support für: `is_private`, `delete`, `unassign`

**Frontend:**
- Erweitere `BulkAssignBar.tsx` um neue Buttons
- "Als privat markieren" / "Als Standard markieren"
- "Zuweisung entfernen" / "Löschen"

### 3. Stammdaten-Management
**Ziel:** Bidirektionaler CSV-Austausch + CRUD-UI

**Backend:**
- `POST /projects`, `PUT /projects/{id}`, `DELETE /projects/{id}`
- `POST /milestones`, `PUT /milestones/{id}`, `DELETE /milestones/{id}`
- `GET /export/projects` - CSV-Export

**Frontend:**
- Neuer Admin-Tab "Stammdaten"
- Tabellen-View mit Inline-Editing
- CSV-Upload & Export

### 4. Telefonbuch-Management
**Ziel:** Automatische Namensauflösung für Anrufer

**Backend:**
- Neues Modell `PhoneBook(id, name, number, company, tags, user_id)`
- CSV-Import/Export
- Lookup-Endpoint: `GET /phonebook/lookup/{number}`
- Auto-Matching in CallLog-Service

**Frontend:**
- Admin-Tab "Telefonbuch"
- CSV-Upload
- Tabellen-View mit Suche

## 🔧 Tech-Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Frontend:** React 18 + TypeScript + Vite + TailwindCSS
- **Windows Agent:** Python 3.11 + pystray (→ PyQt6)
- **Deployment:** Docker Compose auf Raspberry Pi

## 📁 Projekt-Struktur

```
TimeTrack/
├── backend/app/
│   ├── routers/        # API-Endpoints
│   ├── integrations/   # Teams, Placetel
│   ├── models.py       # SQLAlchemy
│   ├── schemas.py      # Pydantic
│   └── services.py     # Business Logic
├── frontend/src/
│   ├── components/     # React-Komponenten
│   ├── App.tsx         # Page-Routing
│   └── api.ts          # HTTP-Client
└── windows_agent/
    ├── main.py         # Entry Point
    └── call_sync.py    # Call-Sync-Thread
```

## 🎨 UI/UX-Guidelines

- **Dark Mode:** Alle Komponenten mit `dark:` Varianten (Tailwind)
- **Responsive:** Mobile-first
- **Toasts:** react-hot-toast für Feedback
- **Colors:** Blue (primary), Slate (grays), Red (errors), Green (success)
- **Icons:** Emojis oder SVG-Icons

## 📊 Wichtige Datenmodelle

### Event
- `source_type`: window | phone | bluetooth
- `is_private`: bool (Privacy-Flag)

### CallLog ✨
- `source`: BLUETOOTH_PBAP | TEAMS | PLACETEL | MANUAL
- `direction`: INBOUND | OUTBOUND | INTERNAL
- `remote_number`, `remote_name`

### Assignment
- Event → Project → Milestone
- `activity_type`, `comment`

## ⚡ Performance-Richtlinien

**WICHTIG:** System läuft auf Raspberry Pi (Low-Power)!

- **LIMIT:** Immer Limits setzen (500-1000)
- **Filter:** Zeitbasierte Filter für Events/Assignments
- **Lazy Loading:** Nur aktive Page lädt Daten
- **Virtual Scrolling:** Für große Tabellen (react-window)
- **Memoization:** React.memo(), useMemo(), useCallback()

## 🔑 Coding-Standards

### Backend
- Type Hints für alle Funktionen
- Pydantic für Input-Validierung
- `HTTPException(status_code=..., detail=...)`
- Dependency Injection: `Depends(get_db)`

### Frontend
- TypeScript strict mode
- Functional Components + Hooks
- Props-Interfaces
- Error Handling: try/catch + toast

### Naming
- Backend: `snake_case`
- Frontend: `camelCase`
- Komponenten: `PascalCase`

## 🚀 Development-Workflow

```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev  # Port 5173

# Windows Agent (auf Windows)
cd windows_agent
python main.py
```

## 📚 API-Dokumentation

- Swagger UI: http://localhost:8000/docs
- Vollständige Endpoint-Liste in `CLAUDE_HANDOVER.md`

## 🐛 Debugging

- **Backend-Logs:** `docker compose logs -f api`
- **Frontend-Logs:** Browser DevTools Console
- **Database:** `backend/data/timetrack.db` (SQLite Browser)

## 💡 Best Practices

1. **Kleine Commits:** Atomare Changes, klare Messages
2. **Testing:** Lokal testen vor Docker-Build
3. **Dark Mode:** Immer testen (Toggle im Burger Menu)
4. **Performance:** Raspberry Pi → LIMIT, Filter, Pagination!
5. **Konsistenz:** Bestehende Komponenten als Vorlage (z.B. AdminPage-Tabs)

## 🎯 Wie du vorgehen solltest

1. **Context:** Lies `CLAUDE_HANDOVER.md` komplett
2. **Feature wählen:** Aus Prioritäten-Liste oben
3. **Recherche:** Schau dir ähnliche Komponenten an
4. **Implementierung:** Backend → Frontend → Testing
5. **Performance:** Optimiere für Raspberry Pi
6. **Commit:** Kleiner, atomarer Commit mit klarer Message

## 📝 Commit-Message-Format

```
feat: Add bulk privacy marking for events
fix: Optimize assignments query for Raspberry Pi
refactor: Migrate tray app to PyQt6 GUI
docs: Update API documentation for phonebook
```

---

**Start hier:**
1. Lies `CLAUDE_HANDOVER.md`
2. Wähle Feature aus Prioritäten
3. Frage bei Unklarheiten nach
4. Implementiere + Teste + Committe

**Bei Fragen:**
- "Zeig mir ähnliche Komponenten für [X]"
- "Wie ist [Y] aktuell implementiert?"
- "Was ist der beste Ansatz für [Z]?"

**WICHTIG:** Performance immer im Blick (Raspberry Pi)!
