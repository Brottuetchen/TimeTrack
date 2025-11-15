# Offline USB-Setup (Pi ↔ Windows)

Ziel: Raspberry Pi 5 stellt API + Web-UI bereit und ist ausschließlich per USB-Ethernet mit dem Windows-PC verbunden. Das Firmen-LAN/WLAN bleibt aktiv; nur Events/Review laufen über das private USB-Link.

## 1. Raspberry Pi vorbereiten

1. `/boot/config.txt` öffnen und `dtoverlay=dwc2` ergänzen.
2. `/etc/modules`:
   ```
   dwc2
   g_ether
   ```
3. `/etc/dhcpcd.conf` erweitern:
   ```
   interface usb0
     static ip_address=192.168.7.2/24
   ```
4. `sudo reboot`.
5. Pi über den USB-C-OTG-Port (neben HDMI) mit dem Windows-PC verbinden. Stromversorgung läuft über dasselbe Kabel.

## 2. Docker-Services starten

```bash
cd /home/pi/TimeTrack
docker compose up -d --build
```

- API: `http://192.168.7.2:8000`
- Web-UI: `http://192.168.7.2:3000`
- SQLite liegt im Volume `timetrack-data`
- Logs: `docker compose logs -f api` bzw. `docker compose logs -f web`

## 3. Windows-Adapter konfigurieren

1. Pi per USB verbinden → Windows installiert „USB Ethernet/RNDIS Gadget“.
2. Adaptereigenschaften → IPv4 statisch:
   - IP: `192.168.7.1`
   - Subnetz: `255.255.255.0`
   - Gateway/DNS leer
3. Optional Firewall-Freigabe für diesen Adapter (nur falls notwendig).

Windows routet Ziele `192.168.7.0/24` über USB, alle anderen Ziele wie gewohnt über das Firmen-LAN.

## 4. Tray-Agent deployen

1. `frontend` bauen (`npm run build`) → optional, falls du lokal testen willst.
2. `windows_agent/dist/TimeTrackTray.exe` + `config.json` nach `%USERPROFILE%\TimeTrack` kopieren.
3. `config.json` (Base-URL `http://192.168.7.2:8000`, Machine/User-ID, Filter) anpassen.
4. `TimeTrackTray.exe` starten → Tray-Icon prüfen, „Tracking aktiv“ lassen.
5. Logs & Buffer: `%APPDATA%\TimeTrack\`.

## 5. Verbindung testen

- Browser: `http://192.168.7.2:3000` (UI) bzw. `http://192.168.7.2:8000/health`.
- Tray-Menü → „Offene Events senden“ nach ein paar Fensterswitches; in der UI sollten neue Einträge erscheinen.

Damit laufen Call-Logger (Bluetooth), Window-Agent (USB) und Review-UI komplett offline; nur das USB-Kabel und iPhone-Bluetooth sind notwendig.

