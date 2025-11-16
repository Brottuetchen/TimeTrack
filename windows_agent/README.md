# Windows Tray Agent (Offline USB Mode)

Dieses Tool läuft auf einem Windows-PC im System-Tray, beobachtet das aktive Fenster und sendet Events über die USB-Ethernet-Verbindung zum Raspberry Pi (Standard `http://192.168.7.2:8000`). Es blockiert oder verändert das reguläre Firmennetzwerk **nicht** – der Agent nutzt nur HTTP-Requests zum Pi und lässt alle anderen Interfaces unangetastet.

## Komponenten

- `main.py` – eigentliche Tray-App (pystray + pywin32). Pollt das aktive Fenster, führt Whitelist/Blacklist und bündelt Aktivitäten in Sessions (`timestamp_start`/`timestamp_end`).
- `config.json` – lokale Konfiguration pro Benutzer (User/Machine-ID, Poll-Intervall, Filter, Backend-URL).
- `requirements.txt` – Python-Abhängigkeiten für Dev/Test oder PyInstaller-Build.
- Portable Build via `pyinstaller` → `TimeTrackTray.exe`, lauffähig ohne Admin/C++ Runtime.

## Features

- System-Tray Menü: Start/Stop Tracking, Status-Anzeige, „Send last hour“.
- Lokaler Puffer (JSON-Datei in `%APPDATA%\TimeTrack\buffer.json`), damit Events auch bei Pi-Ausfall nicht verloren gehen.
- HTTPS optional (einfach Base-URL ändern, Zertifikatsprüfung kann konfiguriert werden).

## Netzwerk/USB-Setup

1. Pi als USB-Ethernet-Gadget konfigurieren (`usb0` = `192.168.7.2`). Windows-Adapter statisch auf `192.168.7.1`.
2. `config.json` → `base_url`: `http://192.168.7.2:8000`.
3. Traytool benötigt nur Zugriff auf diesen Adapter. Der Firmen-Adapter bleibt aktiv; Windows routet Requests anhand der Ziel-IP, daher kein Konflikt.

## Entwicklung

```powershell
cd windows_agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config.example.json config.json
pythonw main.py   # startet ohne Konsolenfenster
```

## Portable Build

```powershell
pyinstaller --noconfirm --onefile --windowed --name TimeTrackTray main.py
```

Resultat: `dist\TimeTrackTray.exe`. Diese Datei zusammen mit `config.json` auf den Ziel-PC kopieren (z. B. USB-Stick). Keine Installationsrechte erforderlich.

## Tray-Steuerung

- **Tracking aktiv** – Menüeintrag mit Häkchen zum Pausieren/Fortsetzen.
- **Offene Events senden** – sofortiger Upload des Puffers.
- **Status anzeigen** – Popup mit aktuellem Zustand (offene Events, letzter Upload, letzter Fehler).
- **Privacy/Filter** – Agent zieht Whitelist/Blacklist + Privacy-Zeitfenster automatisch von `/settings/logging` und stoppt das Logging während des Privacy-Modus.
- **Config öffnen / Logdatei öffnen** – startet automatisch den Editor/Viewer mit den jeweiligen Dateien.
- **Beenden** – stoppt Tray, Tracker und Sender sauber.

Das Icon zeigt grün (aktiv) bzw. orange (pausiert); Tooltip aktualisiert sich automatisch. Verpackt mit `pyinstaller --windowed` läuft das Tool vollständig im Tray.

## Filter-Verwaltung und Priorität

Der Agent unterstützt zwei Arten von Filtern: **Remote-Filter** (aus dem Web-UI) und **lokale Filter** (aus `config.json`).

### Filter-Priorität (wichtig!)

**Remote-Filter haben IMMER Vorrang vor lokalen Filtern:**

1. **Whitelist-Logik:**
   - Wenn eine **Remote-Whitelist** (Web-UI → Privacy Settings) gesetzt ist, werden **NUR** diese Prozesse getrackt
   - Lokale `include_processes` aus `config.json` werden in diesem Fall **IGNORIERT**
   - Wenn die Remote-Whitelist **leer** ist, wird auf lokale `include_processes` zurückgegriffen
   - Wenn **beide leer** sind, werden **alle** Prozesse getrackt (außer Blacklist)

2. **Blacklist-Logik:**
   - Remote-Blacklist (Web-UI) und lokale `exclude_processes` werden **kombiniert**
   - Ein Prozess wird blockiert, wenn er in **einer** der beiden Blacklists steht

### Empfohlene Nutzung

**✅ Empfohlen:** Filter im **Web-UI verwalten** (Privacy Settings)
- Zentrale Verwaltung über das Web-UI
- Änderungen werden automatisch vom Agent abgerufen (alle 60 Sekunden)
- Keine manuelle Bearbeitung von `config.json` nötig

**⚠️ Legacy:** Filter in `config.json` (nur für Offline-Betrieb)
- Nur als Fallback, wenn keine API-Verbindung besteht
- `include_processes` wird ignoriert, sobald Remote-Whitelist gesetzt ist
- `exclude_processes` wird mit Remote-Blacklist kombiniert

### Beispiele

**Szenario 1: Remote-Whitelist LEER (Standard)**
```
Remote-Whitelist: []
Lokale include_processes: ["excel.exe"]
→ Agent trackt ALLES (lokale Whitelist wird IGNORIERT)
```

**Szenario 2: Remote-Whitelist gesetzt**
```
Remote-Whitelist: ["chrome.exe", "acad.exe"]
Lokale include_processes: ["excel.exe"]
→ Agent trackt NUR chrome.exe und acad.exe (lokale Whitelist wird IGNORIERT)
```

**Szenario 3: Blacklist kombiniert**
```
Remote-Blacklist: ["game.exe"]
Lokale exclude_processes: ["spotify.exe"]
→ Agent trackt ALLES außer game.exe UND spotify.exe
```

**Szenario 4: Offline-Betrieb (keine API-Verbindung)**
```
Remote-Whitelist: [] (leer, weil keine Verbindung)
Lokale include_processes: ["excel.exe", "word.exe"]
→ Agent trackt NUR excel.exe und word.exe (Fallback auf lokale Config)
```

### Logging und Debugging

Der Agent loggt beim Start, welche Filter aktiv sind:

```
ACTIVE FILTER: Remote whitelist (Web-UI) → ['chrome.exe', 'acad.exe']
ACTIVE FILTER: Local include_processes will be IGNORED (remote whitelist has priority)
ACTIVE FILTER: Remote blacklist (Web-UI) → ['game.exe']
ACTIVE FILTER: Local blacklist (config.json) → ['spotify.exe']
```

Bei jedem gefilterten Prozess wird im Log (Debug-Level) angegeben, warum er gefiltert wurde:
- "Filtered by remote whitelist: firefox.exe not in ['chrome.exe', 'acad.exe']"
- "Filtered by local whitelist: notepad.exe not in ['excel.exe']"
- "Filtered by remote blacklist: game.exe"

### Agent-Config herunterladen (optional)

Das Web-UI bietet einen Endpoint `GET /settings/agent-config`, der eine fertige `config.json` mit den aktuellen Remote-Filtern generiert. Diese kann heruntergeladen und als Basis für die lokale Config verwendet werden.

## Start auf Firmenrechner

1. `config.json` mit Firmen-spezifischen Werten (User-ID, Projekt-Filter) befüllen.
2. Pi via USB anschließen (Adapter zeigt „verbunden“).
3. `TimeTrackTray.exe` doppelklicken → Icon erscheint. „Tracking aktiv“ sollte grün sein.
4. Backend-UI im Browser: `http://192.168.7.2:3000` (sobald Frontend-Container steht). Bis dahin: FastAPI-Docs via `http://192.168.7.2:8000/docs`.
