"""
Debug-Tool für TimeTrack Windows Agent
Führt Verbindungs- und Konfigurations-Checks durch
"""
import json
import sys
from pathlib import Path

import requests


def main():
    print("=" * 60)
    print("TimeTrack Windows Agent - Debug Tool")
    print("=" * 60)
    print()

    # 1. Config laden
    config_path = Path(__file__).with_name("config.json")
    if not config_path.exists():
        print("❌ config.json nicht gefunden!")
        return

    print("✓ config.json gefunden")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    print(f"  Base URL: {config['base_url']}")
    print(f"  User ID: {config['user_id']}")
    print(f"  Machine ID: {config['machine_id']}")
    print()

    # 2. Log-Datei Check
    appdata_path = str(Path.home() / "AppData" / "Roaming")
    log_file = config.get("log_file", "").replace("%APPDATA%", appdata_path)
    log_path = Path(log_file)
    if log_path.exists():
        print(f"✓ Log-Datei gefunden: {log_path}")
        size_kb = log_path.stat().st_size / 1024
        print(f"  Größe: {size_kb:.1f} KB")

        # Letzte 10 Zeilen
        print("\n  Letzte 10 Log-Zeilen:")
        print("  " + "-" * 50)
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(f"  {line.rstrip()}")
        print()
    else:
        print(f"⚠ Log-Datei nicht gefunden: {log_path}")
        print()

    # 3. Buffer Check
    buffer_file = config.get("buffer_file", "").replace("%APPDATA%", appdata_path)
    buffer_path = Path(buffer_file)
    if buffer_path.exists():
        buffer = json.loads(buffer_path.read_text(encoding="utf-8"))
        print(f"✓ Buffer gefunden: {len(buffer)} Event(s) wartend")
        if buffer:
            print(f"  Ältester: {buffer[0].get('process_name', 'unknown')}")
            print(f"  Neuester: {buffer[-1].get('process_name', 'unknown')}")
        print()
    else:
        print(f"⚠ Buffer nicht gefunden: {buffer_path}")
        print()

    # 4. Backend Verbindung testen
    base_url = config["base_url"]
    print(f"Backend-Verbindungstest zu {base_url}...")

    try:
        # Health Check
        resp = requests.get(f"{base_url}/health", timeout=5, verify=False)
        if resp.status_code == 200:
            print(f"✓ Health Check OK: {resp.json()}")
        else:
            print(f"⚠ Health Check fehlgeschlagen: HTTP {resp.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Verbindung fehlgeschlagen! Backend nicht erreichbar.")
        print(f"   Stelle sicher, dass das Backend läuft auf {base_url}")
    except requests.exceptions.Timeout:
        print(f"❌ Timeout! Backend antwortet nicht.")
    except Exception as e:
        print(f"❌ Fehler: {e}")

    print()

    # 5. Test Event senden
    print("Test-Event senden...")
    test_event = {
        "timestamp_start": "2025-11-15T12:00:00Z",
        "timestamp_end": "2025-11-15T12:00:05Z",
        "duration_seconds": 5,
        "window_title": "DEBUG TEST",
        "process_name": "notepad.exe",
        "machine_id": config["machine_id"],
        "user_id": config["user_id"]
    }

    try:
        resp = requests.post(
            f"{base_url}/events/window",
            json=test_event,
            timeout=10,
            verify=False
        )
        if resp.status_code < 300:
            print(f"✓ Test-Event erfolgreich gesendet! HTTP {resp.status_code}")
        else:
            print(f"❌ Test-Event fehlgeschlagen: HTTP {resp.status_code}")
            print(f"   Response: {resp.text}")
    except Exception as e:
        print(f"❌ Fehler beim Senden: {e}")

    print()
    print("=" * 60)
    print("Debug-Check abgeschlossen!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    input("\nDrücke Enter zum Beenden...")
