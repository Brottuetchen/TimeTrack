import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import List, Tuple


class BluetoothError(Exception):
    pass


def _run(command: List[str], input_data: str | None = None, timeout: int = 30) -> Tuple[int, str, str]:
    try:
        result = subprocess.run(
            command,
            input=input_data,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise BluetoothError(f"Befehl nicht gefunden: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise BluetoothError(f"Befehl zeitueberschreitung: {' '.join(command)}") from exc
    return result.returncode, result.stdout, result.stderr


def run_bluetoothctl_script(commands: List[str], timeout: int = 30) -> Tuple[int, str, str]:
    script = "\n".join(commands + ["quit\n"])
    return _run(["bluetoothctl"], input_data=script, timeout=timeout)


def scan_devices(timeout: int = 8) -> List[dict]:
    _run(["bluetoothctl", "--timeout", str(timeout), "scan", "on"], timeout=timeout + 2)
    code, stdout, stderr = _run(["bluetoothctl", "devices"], timeout=10)
    if code != 0:
        raise BluetoothError(stderr.strip() or "Scan fehlgeschlagen")
    devices = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("Device "):
            continue
        parts = line.split(" ", 2)
        if len(parts) >= 3:
            devices.append({"mac": parts[1], "name": parts[2]})
    return devices


def list_devices() -> List[dict]:
    code, stdout, stderr = _run(["bluetoothctl", "devices"], timeout=10)
    if code != 0:
        raise BluetoothError(stderr.strip() or "Geraeteliste fehlgeschlagen")
    devices = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("Device "):
            continue
        parts = line.split(" ", 2)
        if len(parts) >= 3:
            devices.append({"mac": parts[1], "name": parts[2]})
    return devices


def pair_device(mac: str) -> Tuple[str, str]:
    script = textwrap.dedent(
        f"""
        pair {mac}
        trust {mac}
        """
    )
    code, stdout, stderr = run_bluetoothctl_script(script.strip().splitlines())
    if code != 0:
        raise BluetoothError(stderr.strip() or "Pairing fehlgeschlagen")
    return stdout, stderr


def connect_device(mac: str) -> Tuple[str, str]:
    code, stdout, stderr = run_bluetoothctl_script([f"connect {mac}"])
    if code != 0:
        raise BluetoothError(stderr.strip() or "Connect fehlgeschlagen")
    return stdout, stderr


def disconnect_device(mac: str) -> Tuple[str, str]:
    code, stdout, stderr = run_bluetoothctl_script([f"disconnect {mac}"])
    if code != 0:
        raise BluetoothError(stderr.strip() or "Disconnect fehlgeschlagen")
    return stdout, stderr


def pbap_sync(mac: str) -> dict:
    tmp = Path(tempfile.gettempdir()) / "timetrack_pbap.vcf"
    script = textwrap.dedent(
        f"""
        connect {mac} PBAP
        get telecom/callhistory.vcf {tmp}
        """
    )
    code, stdout, stderr = _run(["obexctl"], input_data=script + "\nquit\n", timeout=45)
    if code != 0:
        raise BluetoothError(stderr.strip() or stdout.strip() or "PBAP Sync fehlgeschlagen")
    size = tmp.stat().st_size if tmp.exists() else 0
    return {"path": str(tmp), "bytes": size, "stdout": stdout, "stderr": stderr}

