# TimeTrack MVP

Offline-fähiges Zeiterfassungssystem (Pi 5 + iPhone + Windows-Agent) mit FastAPI-Backend, React-Web-UI, Bluetooth-Call-Logging und CSV-Export.

## Ordnerstruktur

- `backend/` – FastAPI + SQLite + Dockerfile
- `frontend/` – React/Vite Web-UI (Events reviewen & zuweisen)
- `windows_agent/` – Tray-Agent für Fensterevents (Python/PyInstaller)
- `pi_services/call_logger/` – Bluetooth Call-Logger (oFono + pydbus)
- `docs/` – USB-Offline-Setup
- `docker-compose.yml` – startet API + Web-UI auf dem Pi

## Schnellstart (Raspberry Pi 5)

```bash
git clone <repo> ~/TimeTrack
cd ~/TimeTrack
docker compose up -d --build
```

- API → `http://<pi-ip>:8000`
- Web-UI → `http://<pi-ip>:3000`
- Datenbank → `timetrack-data` Volume (SQLite)

## Demo-Daten einspielen

```bash
python scripts/seed_dummy_data.py --base-url http://localhost:8000 --days 14 --windows-per-day 6 --calls-per-day 3
```

- API muss laufen (lokal oder auf dem Pi via USB-IP).
- Script legt Beispiel-Projekte, -Milestones, viele Events über den angegebenen Zeitraum sowie Zuordnungen an, damit du das UI sofort testen kannst.
- Parameter `--base-url`, `--user-id`, `--machine-id`, `--device-id` passen die Demo-Daten an.
- Mit `--days`, `--windows-per-day`, `--calls-per-day` steuerst du Zeitspanne und Menge (Standard: 10 Tage, 5 Fenster-Events/Tag, 2 Calls/Tag).
- Am einfachsten im bestehenden Backend-Venv ausführen (`cd backend && .\.venv\Scripts\activate`), dort ist `requests` bereits installiert.

## Windows-Tray-Agent

```powershell
cd windows_agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config.example.json config.json
python main.py
```

Für Portable Build:

```powershell
pyinstaller --noconfirm --onefile --windowed --name TimeTrackTray main.py
```

Config (`config.json`) anpassen (Base-URL `http://192.168.7.2:8000`, Filter etc.). Das Tool sendet nur über das USB-Subnetz.

## Bluetooth Call-Logger

```bash
sudo apt install -y bluez bluez-tools ofono python3-gi python3-dbus
cd pi_services/call_logger
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
sudo cp timetrack-call-logger.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now timetrack-call-logger
```

Pairing headless mit `bluetoothctl` (siehe `pi_services/call_logger/README.md`). Reconnect-Skript per systemd-Timer konfigurieren.

## Web-UI Entwicklung

```bash
cd frontend
npm install
npm run dev -- --host
```

`VITE_API_BASE` (oder Port 8000) per `.env` steuern. `npm run build` erzeugt `dist/` (Docker nutzt nginx).

### Projekte/Milestones per CSV importieren

- UI → Karte „Projekte / Milestones via CSV“ → Datei auswählen und hochladen.
- Akzeptiert z. B. `C:\Users\trapp\Downloads\gesamt.csv` mit Spalten aus deinem ERP.
- Mindestens eine der Spalten `project_name` oder `Projekte` muss gesetzt sein.
- Optional: `kunde`, `notizen`, `milestone_name`/`Arbeitspaket`, `Sollstunden`, `Erbrachte Stunden`, `bonus_relevant`. Alle weiteren Felder werden ignoriert.
- `Sollstunden`/`Erbrachte Stunden` dürfen Dezimalzahlen mit Komma oder Punkt enthalten; sie landen als Stundenwerte direkt am Milestone (`soll_stunden`, `ist_stunden`).
- UI besitzt einen Dark-Mode-Toggle (rechts oben, ☀️/🌙) — Zustand wird lokal gespeichert.
- Activity-Auswahl ist jetzt ein Dropdown (Planung/Baustelle/…); bei Telefon-Events wird automatisch „Telefon“, bei Fenster-Events „PC“ vorgeschlagen. Kommentare werden initial aus den Eventdaten befüllt (z. B. „Anruf Kunde Müller (+4917…)“ oder „Fenster AutoCAD – Werkhalle.dwg“), können aber jederzeit überschrieben werden.
- Bluetooth-Setup-Karte zeigt die wichtigsten Pairing-/PBAP-Kommandos inkl. Copy-Buttons direkt im UI, damit du iPhone und Pi ohne Docs neu verbinden kannst.

## Offline-USB Betriebsmodus

Schritt-für-Schritt-Anleitung: `docs/offline_usb_setup.md`. Kurzfassung:

1. Pi als USB-Ethernet-Gadget (192.168.7.2) konfigurieren.
2. Windows-Adapter statisch auf 192.168.7.1 setzen.
3. `docker compose up -d --build` (API 8000, UI 3000).
4. Tray-Agent + Browser greifen über `http://192.168.7.2` zu.

## CSV Export / API

- Export-Endpoint: `GET /export/csv?start=...&end=...` (Spalten siehe `backend/app/routers/export.py`).
- Events/Zuordnungen bearbeitbar im Web-UI (Bulk & Inline).

## Tests / Health

- API Health: `GET /health`
- Web-UI Build: `npm run build`
- Tray-Agent Logging: `%APPDATA%\TimeTrack\`
- Call-Logger Logs: `journalctl -u timetrack-call-logger -f`

Alles bleibt lokal/offline, bis du CSV exportierst und manuell importierst.

- Privacy/Filter-Karte im UI verwaltet Whitelist/Blacklist sowie den Privacy-Modus (Logging 15/30 Minuten oder unbegrenzt pausieren). Der Windows-Agent pollt `/settings/logging` und respektiert diese Vorgaben automatisch.
- **Filter-Priorität:** Remote-Filter aus dem Web-UI haben **immer Vorrang** vor lokalen Filtern aus `config.json`. Wenn eine Remote-Whitelist gesetzt ist, werden lokale `include_processes` ignoriert. Details siehe `windows_agent/README.md`.
- **Agent-Config Download:** `GET /settings/agent-config` liefert eine fertige `config.json` mit den aktuellen Remote-Filtern zum Download.
