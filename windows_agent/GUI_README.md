# TimeTrack Windows Agent - PyQt6 GUI

## 🎨 Neue Features

Die PyQt6-GUI-Version bietet eine vollwertige grafische Benutzeroberfläche statt des bisherigen CLI-Tray-Menüs.

### Features

- ✅ **System Tray Integration** mit modernem Icon (grün=aktiv, orange=pausiert)
- ✅ **Dashboard** mit Live-Event-Preview (letzte 10 Events)
- ✅ **Quick-Assign Dialog** zum schnellen Zuweisen von Events
- ✅ **Settings Dialog** für Whitelist/Blacklist, Privacy-Mode, Call-Sync
- ✅ **Dark Mode** für alle GUI-Komponenten
- ✅ **System-Notifications** für wichtige Events
- ✅ **Call-Sync Status** Anzeige (Teams/Placetel)

## 📦 Installation

### Voraussetzungen

- Python 3.11+
- Windows 10/11

### Dependencies installieren

```bash
cd windows_agent
pip install -r requirements.txt
```

Die `requirements.txt` enthält jetzt auch PyQt6:

```
pywin32==306
requests==2.31.0
pystray==0.19.5
Pillow==10.1.0
psutil==5.9.5
PyQt6==6.6.1
PyQt6-Qt6==6.6.1
```

## 🚀 Verwendung

### GUI-Version starten (Empfohlen)

```bash
python main_qt.py
```

### CLI-Version starten (Legacy)

```bash
python main.py
```

## 🎯 GUI-Komponenten

### 1. System Tray Icon

**Rechtsklick auf Icon:**
- Dashboard öffnen
- Quick-Assign
- Tracking aktiv/pausieren
- Events jetzt senden
- Call-Sync jetzt (falls aktiviert)
- Einstellungen
- Status anzeigen
- Beenden

**Doppelklick auf Icon:**
- Öffnet Dashboard

**Icon-Farben:**
- 🟢 Grün: Tracking aktiv
- 🟠 Orange: Tracking pausiert

### 2. Dashboard

**Tab: Dashboard**
- Live-Event-Tabelle (letzte 10 Events)
- Tagesstatistiken (Events, Offene Events, Privacy-Status)
- Auto-Refresh alle 10 Sekunden
- Manueller Refresh-Button

**Tab: Call-Sync** (falls aktiviert)
- Call-Sync Status
- Letzte Synchronisation
- Nächster Sync-Zeitpunkt

**Header-Buttons:**
- Quick-Assign
- Einstellungen

### 3. Quick-Assign Dialog

**Features:**
- Multi-Select Event-Tabelle (letzte 20 unzugewiesene Events)
- Projekt-Auswahl (Dropdown)
- Milestone-Auswahl (abhängig vom Projekt)
- Aktivitätstyp (Planung, Baustelle, Dokumentation, Meeting, Fahrt, Telefon, PC)
- Kommentar-Feld
- Bulk-Assignment (mehrere Events gleichzeitig)

**Workflow:**
1. Events in Tabelle auswählen (Mehrfachauswahl mit Strg/Shift)
2. Projekt wählen
3. Milestone wählen (optional)
4. Aktivitätstyp wählen
5. Kommentar eingeben (optional)
6. "Zuweisen" klicken

### 4. Settings Dialog

**Tab: Privacy & Filter**

**Privacy-Mode:**
- Status-Anzeige (aktiv/pausiert)
- "30 Min pausieren" Button
- "Fortsetzen" Button

**Whitelist:**
- Liste aller whitelisted Prozesse
- Hinzufügen/Entfernen von Prozessen
- Nur diese Prozesse werden getrackt (leer = alle)

**Blacklist:**
- Liste aller blacklisted Prozesse
- Hinzufügen/Entfernen von Prozessen
- Diese Prozesse werden NICHT getrackt

**Tab: Call-Sync**

**Microsoft Teams:**
- Aktivieren/Deaktivieren
- Tenant ID
- Client ID
- Client Secret (Password-Feld)

**Placetel:**
- Aktivieren/Deaktivieren
- API-Key (Password-Feld)

**Speichern:**
- Speichert alle Einstellungen im Backend
- Backend-Sync erfolgt automatisch

## 🎨 Dark Mode

Alle GUI-Komponenten sind im Dark Mode gestaltet:
- Hintergrund: `#1e1e1e` (dunkelgrau)
- Text: `#e0e0e0` (hellgrau)
- Primary: `#0d7377` (türkis)
- Hover: `#14a085` (helles türkis)
- Borders: `#3a3a3a` (mittelgrau)

## 🔧 Architektur

### Komponenten-Struktur

```
windows_agent/
├── main.py             # Legacy CLI-Version
├── main_qt.py          # ✨ PyQt6 GUI-Version
├── call_sync.py        # Call-Sync-Manager (unverändert)
└── gui/
    ├── __init__.py
    ├── tray_controller.py      # System Tray Controller
    ├── main_window.py          # Dashboard-Fenster
    ├── dashboard_widget.py     # Dashboard mit Live-Events
    ├── quick_assign_dialog.py  # Quick-Assign Dialog
    └── settings_dialog.py      # Settings Dialog
```

### Thread-Architektur

Die bestehenden Background-Threads bleiben unverändert:
- `WindowTracker` - Trackt aktive Fenster
- `EventSender` - Sendet Events an Backend
- `RemoteSettingsManager` - Sync von Backend-Settings
- `CallSyncManager` - Sync von Teams/Placetel Calls

PyQt6 fügt hinzu:
- `QApplication` - Qt Event Loop
- `QTimer` - Periodische GUI-Updates

### Signal/Slot-Kommunikation

```python
# TrayController Signals
dashboard_requested → QtApp._show_dashboard()
quick_assign_requested → QtApp._show_quick_assign()
settings_requested → QtApp._show_settings()
tracking_toggled → QtApp._toggle_tracking()
send_now_requested → QtApp._send_now()
call_sync_requested → QtApp._trigger_call_sync()
quit_requested → QtApp.quit()
```

## 🐛 Debugging

### Logs

Logs werden weiterhin in `timetrack_agent.log` geschrieben (siehe `config.json`).

```bash
# Tail Logs
tail -f %APPDATA%/TimeTrack/timetrack_agent.log
```

### Häufige Probleme

**1. PyQt6 Import Error**
```
ModuleNotFoundError: No module named 'PyQt6'
```
→ Lösung: `pip install PyQt6==6.6.1 PyQt6-Qt6==6.6.1`

**2. Dashboard lädt keine Events**
→ Prüfe Backend-URL in `config.json`
→ Prüfe Backend-Logs: `docker compose logs -f api`

**3. Quick-Assign zeigt keine Projekte**
→ Prüfe, ob Projekte im Backend existieren
→ API-Key korrekt in `config.json`?

**4. Settings Dialog speichert nicht**
→ Prüfe Backend `/settings/logging` Endpoint
→ Prüfe Logs auf HTTP-Fehler

## 🔄 Migration von CLI zu GUI

### Schritt 1: Dependencies installieren

```bash
pip install PyQt6==6.6.1 PyQt6-Qt6==6.6.1
```

### Schritt 2: GUI-Version testen

```bash
# Stoppe alte CLI-Version
# (Tray-Icon Rechtsklick → Beenden)

# Starte neue GUI-Version
python main_qt.py
```

### Schritt 3: Autostart anpassen (optional)

Wenn du Autostart nutzt, ändere den Pfad:

**Vorher:**
```
python C:\path\to\TimeTrack\windows_agent\main.py
```

**Nachher:**
```
python C:\path\to\TimeTrack\windows_agent\main_qt.py
```

## 📊 Performance

Die GUI-Version ist minimal ressourcenintensiver als die CLI-Version:

| Komponente | CLI | GUI |
|------------|-----|-----|
| RAM | ~30 MB | ~50 MB |
| CPU (Idle) | <1% | <1% |
| CPU (Active) | ~2% | ~3% |

→ Vernachlässigbar für moderne PCs

## 🎯 Roadmap

### Geplante Features

- [ ] Offline-Mode mit lokaler Queue
- [ ] WebSocket für Echtzeit-Updates
- [ ] Benachrichtigungen bei wichtigen Events
- [ ] Mini-Kalender für Zeitraumauswahl
- [ ] Event-Bearbeitung direkt im Dashboard
- [ ] Export-Funktion (CSV, PDF)

## 💡 Best Practices

1. **Tracking Pause:** Nutze Privacy-Mode statt Agent zu beenden
2. **Quick-Assign:** Multi-Select für schnellere Bulk-Zuweisungen
3. **Whitelist:** Für fokussiertes Tracking nur relevante Prozesse
4. **Dashboard:** Lasse Dashboard offen für Live-Monitoring

## 🆘 Support

Bei Problemen:
1. Prüfe Logs: `timetrack_agent.log`
2. Prüfe Backend-Logs: `docker compose logs -f api`
3. Erstelle Issue auf GitHub mit:
   - Log-Auszug
   - Screenshot (falls GUI-Problem)
   - Config (ohne Secrets!)

---

**Version:** 1.0.0 (PyQt6)
**Letztes Update:** 2025-11-15
**Kompatibilität:** Windows 10/11, Python 3.11+
