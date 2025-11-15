# Bluetooth Call Logger (Pi ↔ iPhone)

Headless Dienst, der via oFono/BlueZ Telefonate vom iPhone empfängt, live an `/events/phone` sendet und optional über PBAP vergangene Anruflisten nachzieht.

## Voraussetzungen

```bash
sudo apt update
sudo apt install -y bluez bluez-tools ofono bluez-obexd python3-gi python3-dbus python3-pip
sudo systemctl enable --now ofono
```

FastAPI sollte lokal auf `http://127.0.0.1:8000` laufen (oder eigene URL per `TIMETRACK_API` angeben).

## Installation

```bash
cd ~/TimeTrack/pi_services/call_logger
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## systemd-Service

`pi_services/call_logger/timetrack-call-logger.service` anpassen und nach `/etc/systemd/system/` kopieren:

```ini
[Unit]
Description=TimeTrack Bluetooth Call Logger
After=bluetooth.target ofono.service docker.service

[Service]
Type=simple
WorkingDirectory=/home/pi/TimeTrack/pi_services/call_logger
Environment=TIMETRACK_API=http://127.0.0.1:8000
Environment=TIMETRACK_DEVICE_ID=iphone-pi
Environment=TIMETRACK_USER_ID=demo
# Optional: PBAP Sync aktivieren (MAC-Adresse einsetzen)
# Environment=TIMETRACK_PBAP_DEVICE=90:B7:90:3D:03:22
Environment=TIMETRACK_PBAP_STATE=/var/lib/timetrack/pbap_state.json
Environment=TIMETRACK_PBAP_INTERVAL=900
ExecStart=/home/pi/TimeTrack/pi_services/call_logger/.venv/bin/python3 call_logger.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /var/lib/timetrack
sudo systemctl daemon-reload
sudo systemctl enable --now timetrack-call-logger
sudo journalctl -u timetrack-call-logger -f
```

## PBAP (vergangene Anrufe)

Falls `TIMETRACK_PBAP_DEVICE` gesetzt ist, lädt der Dienst regelmäßig `callhistory.vcf` über PBAP und importiert neue Einträge:

1. Beim Pairing dem Pi Zugriff auf Kontakte erlauben.
2. `bluez-obexd` muss laufen (ist Teil der obigen Pakete).
3. `TIMETRACK_PBAP_INTERVAL` (Sekunden) steuert die Sync-Häufigkeit, `TIMETRACK_PBAP_STATE` speichert, welche Einträge schon importiert wurden.

## Headless-Pairing

```bash
sudo bluetoothctl
power on
agent on
default-agent
discoverable on
pairable on
scan on
```

Wenn das iPhone gefunden wird:

```
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
```

Auf dem iPhone den Code bestätigen und „Kontakte & Favoriten“ freigeben. Danach:

```
scan off
exit
```

Optional: Autoconnect per Skript/Timer (siehe `docs/offline_usb_setup.md`).

## Test

```bash
curl -X POST http://127.0.0.1:8000/events/phone \
  -H "Content-Type: application/json" \
  -d '{"timestamp_start":"2024-05-10T09:00:00","timestamp_end":"2024-05-10T09:05:00","direction":"OUTGOING"}'
```

Dann echten Call starten und `journalctl -u timetrack-call-logger -f` beobachten – „Call added / Call finished“ sollten erscheinen und die Einträge tauchen im Web-UI auf.
