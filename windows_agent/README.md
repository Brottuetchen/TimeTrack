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

## Start auf Firmenrechner

1. `config.json` mit Firmen-spezifischen Werten (User-ID, Projekt-Filter) befüllen.
2. Pi via USB anschließen (Adapter zeigt „verbunden“).
3. `TimeTrackTray.exe` doppelklicken → Icon erscheint. „Tracking aktiv“ sollte grün sein.
4. Backend-UI im Browser: `http://192.168.7.2:3000` (sobald Frontend-Container steht). Bis dahin: FastAPI-Docs via `http://192.168.7.2:8000/docs`.
