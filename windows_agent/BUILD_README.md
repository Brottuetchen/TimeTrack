# TimeTrack Agent - EXE Build & Autostart Anleitung

Diese Anleitung erklärt, wie du den TimeTrack Agent als eigenständige EXE-Datei erstellen und ins Windows Autostart-Verzeichnis einrichten kannst.

## 📋 Voraussetzungen

1. Python 3.11 oder höher installiert
2. Alle Dependencies installiert:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```
3. `config.json` erstellt und konfiguriert (siehe `config.example.json`)

## 🔨 Schritt 1: EXE erstellen

### Option A: Automatisch mit Batch-File (empfohlen)

Einfach doppelklicken oder im Terminal ausführen:

```bash
build.bat
```

Das Skript macht folgendes:
- Prüft ob PyInstaller installiert ist (installiert es bei Bedarf)
- Löscht alte Build-Artefakte
- Erstellt die EXE mit PyInstaller
- Kopiert die fertige `TimeTrackAgent.exe` ins Hauptverzeichnis

### Option B: Manuell

```bash
# PyInstaller installieren (falls noch nicht geschehen)
pip install pyinstaller

# EXE erstellen
pyinstaller --clean timetrack_agent.spec

# EXE befindet sich dann in: dist\TimeTrackAgent.exe
```

## 📁 Wichtige Dateien nach dem Build

Nach dem erfolgreichen Build brauchst du folgende Dateien:

```
windows_agent/
├── TimeTrackAgent.exe   ← Die erstellte EXE
├── config.json          ← WICHTIG: Muss im selben Ordner liegen!
└── (optional) logs/
```

**⚠️ WICHTIG:** Die `config.json` muss **immer** im selben Verzeichnis wie die EXE liegen!

## 🚀 Schritt 2: Autostart einrichten

### Option A: Automatisch mit Batch-File (empfohlen)

Doppelklicken oder im Terminal ausführen:

```bash
install_autostart.bat
```

Das Skript erstellt eine Verknüpfung im Windows Autostart-Ordner (`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`).

### Option B: Manuell

1. **Windows-Taste + R** drücken
2. `shell:startup` eingeben und Enter drücken
3. Im geöffneten Ordner: Rechtsklick → Neu → Verknüpfung
4. Pfad zur `TimeTrackAgent.exe` angeben
5. Verknüpfung einen Namen geben (z.B. "TimeTrack Agent")

### Option C: Mit PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File .\install_autostart.ps1
```

## 🗑️ Autostart entfernen

### Option A: Mit Batch-File

```bash
uninstall_autostart.bat
```

### Option B: Mit PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File .\install_autostart.ps1 -Uninstall
```

### Option C: Manuell

1. **Windows-Taste + R** drücken
2. `shell:startup` eingeben und Enter drücken
3. Die Verknüpfung "TimeTrackAgent" löschen

## 🎯 Die EXE nutzen

### Erste Schritte

1. Stelle sicher, dass `config.json` konfiguriert ist
2. Starte `TimeTrackAgent.exe` per Doppelklick
3. Ein grünes Icon erscheint im System-Tray (neben der Uhr)

### Tray-Menü

Rechtsklick auf das Icon zeigt:
- **Tracking aktiv** - Tracking an/aus schalten
- **Offene Events senden** - Manuell senden
- **Status anzeigen** - Statusinfos anzeigen
- **Call-Sync jetzt ausführen** - (falls aktiviert)
- **Config öffnen** - config.json im Editor öffnen
- **Logdatei öffnen** - Log-Datei öffnen
- **Beenden** - Anwendung beenden

### Deployment auf anderen PCs

Wenn du die EXE auf andere PCs verteilen möchtest:

1. Kopiere diese Dateien:
   ```
   TimeTrackAgent.exe
   config.json (oder config.example.json als Vorlage)
   ```

2. Auf dem Ziel-PC:
   - Erstelle einen Ordner (z.B. `C:\Program Files\TimeTrack\`)
   - Kopiere die Dateien hinein
   - Passe `config.json` an (user_id, machine_id, etc.)
   - Führe `install_autostart.bat` aus (oder erstelle manuell eine Verknüpfung)

## 🛠️ Troubleshooting

### "EXE startet nicht" / "Fehlt eine DLL"

Die EXE sollte alle Dependencies enthalten. Falls Probleme auftreten:
- Prüfe ob Visual C++ Redistributable installiert ist
- Führe die EXE in CMD aus um Fehler zu sehen: `TimeTrackAgent.exe`

### "config.json nicht gefunden"

Die `config.json` muss im **selben Ordner** wie die EXE liegen.

### "PyInstaller import error"

```bash
pip install --upgrade pyinstaller
```

### Log-Dateien prüfen

Die Log-Datei wird standardmäßig hier erstellt:
```
%APPDATA%\TimeTrack\timetrack_agent.log
```

Oder je nach Konfiguration in `config.json` unter `log_file`.

### Neustart der Anwendung

Falls du Änderungen an der `config.json` vorgenommen hast:
1. Rechtsklick auf Tray-Icon → Beenden
2. EXE neu starten (oder PC neu starten wenn im Autostart)

## 📝 Konfigurationspfade

Die EXE sucht Dateien relativ zu ihrem Standort:

- `config.json` - im selben Ordner wie die EXE
- `log_file` - wie in config.json angegeben (supports `%APPDATA%`, `~`, etc.)
- `buffer_file` - wie in config.json angegeben

Beispiel config.json:
```json
{
  "log_file": "%APPDATA%\\TimeTrack\\agent.log",
  "buffer_file": "%APPDATA%\\TimeTrack\\buffer.json"
}
```

## 🔐 Sicherheitshinweise

- Die EXE ist **nur für Windows**
- Nicht signiert - Windows Defender könnte warnen
- Bei Bedarf eine Code-Signing-Zertifikat verwenden
- `api_key` und Credentials nie in Git committen!

## 📦 Build-Dateien

Nach dem Build werden folgende Ordner erstellt:
- `build/` - Temporäre Build-Dateien (kann gelöscht werden)
- `dist/` - Fertige EXE (kann gelöscht werden nach Kopieren)

Die Skripte räumen automatisch auf bei jedem Build.

## ✅ Checkliste: Deployment auf neuem PC

- [ ] TimeTrackAgent.exe kopiert
- [ ] config.json erstellt und angepasst
- [ ] user_id und machine_id in config.json gesetzt
- [ ] base_url auf Backend-Server gesetzt
- [ ] EXE testweise gestartet (grünes Icon im Tray?)
- [ ] Autostart eingerichtet (install_autostart.bat)
- [ ] PC neu gestartet und geprüft ob Agent startet

## 🆘 Support

Bei Problemen:
1. Log-Datei prüfen (Tray-Menu → "Logdatei öffnen")
2. Config prüfen (Tray-Menu → "Config öffnen")
3. Status prüfen (Tray-Menu → "Status anzeigen")
4. GitHub Issues: https://github.com/Brottuetchen/TimeTrack/issues
