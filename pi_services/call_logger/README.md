# Bluetooth Call Logger (Pi ↔ iPhone)

## Überblick

- Lauscht per `pydbus` auf `org.ofono.VoiceCallManager`
- Schreibt Telefon-Events direkt in die FastAPI `/events/phone`
- Läuft headless als `systemd`-Service auf dem Pi 5
- Kapselt alles lokal (keine Cloud, kein Firmennetz nötig)

## Voraussetzungen

```bash
sudo apt update
sudo apt install -y bluez bluez-tools ofono python3-gi python3-dbus python3-pip
sudo systemctl enable --now ofono
```

FastAPI/API muss auf `http://127.0.0.1:8000` (oder eigener IP) laufen.

## Installation

```bash
cd ~/TimeTrack/pi_services/call_logger
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Systemd-Service

Datei `pi_services/call_logger/timetrack-call-logger.service` (bereitgestellt in Repo) nach `/etc/systemd/system/` kopieren und Pfade anpassen:

```ini
[Unit]
Description=TimeTrack Bluetooth Call Logger
After=bluetooth.target ofono.service docker.service

[Service]
Type=simple
WorkingDirectory=/home/pi/TimeTrack/pi_services/call_logger
Environment=TIMETRACK_API=http://127.0.0.1:8000
Environment=TIMETRACK_DEVICE_ID=iphone-lars
Environment=TIMETRACK_USER_ID=lars
ExecStart=/home/pi/TimeTrack/pi_services/call_logger/.venv/bin/python call_logger.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now timetrack-call-logger
sudo journalctl -u timetrack-call-logger -f
```

## Headless-Pairing (kein Display nötig)

1. SSH auf den Pi (`ssh pi@timetrack.local`)
2. Start Bluetoothctl:
   ```bash
   sudo bluetoothctl
   power on
   agent on
   default-agent
   discoverable on
   pairable on
   scan on
   ```
3. Auf dem iPhone → Einstellungen → Bluetooth → Pi auswählen.
4. Sobald `scan on` dein iPhone (`XX:XX...`) zeigt:
   ```
   pair XX:XX:XX:XX:XX:XX
   trust XX:XX:XX:XX:XX:XX
   connect XX:XX:XX:XX:XX:XX
   ```
   Auf dem iPhone PIN bestätigen + Zugriff auf Kontakte erlauben.
5. Nach erfolgreichem Connect:
   ```
   scan off
   exit
   ```

### Automatische Reconnects

- Skript `echo "connect XX:XX..." | bluetoothctl` als `/usr/local/bin/iphone_reconnect.sh`.
- Systemd-Timer (`iphone-reconnect.timer`, siehe `docs/offline_usb_setup`) sorgt für tägliche Verbindungen.

## Kontakte (optional)

- PBAP-Dump (sofern iOS erlaubt) via `obexctl`:
  ```bash
  sudo apt install -y obexpushd
  obexctl
  [obex] connect XX:XX... PBAP
  [obex] get phonebook.vcf contacts.vcf
  ```
- VCF konvertieren zu JSON:
  ```bash
  python scripts/vcf_to_json.py contacts.vcf > contacts.json
  ```
- Pfad in `TIMETRACK_CONTACTS=/home/pi/TimeTrack/pi_services/call_logger/contacts.json`.

## Test

```bash
curl -X POST http://127.0.0.1:8000/events/phone -H "Content-Type: application/json" \
  -d '{"timestamp_start":"2024-05-10T09:00:00Z","timestamp_end":"2024-05-10T09:05:00Z","direction":"OUTGOING","device_id":"iphone-test"}'
```

Dann echten Anruf mit dem iPhone starten, `journalctl -u timetrack-call-logger -f` beobachten und prüfen, ob der Event im Backend landet.

