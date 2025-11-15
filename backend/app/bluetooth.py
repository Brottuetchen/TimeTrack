import re
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ANSI_ESCAPE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
DEVICE_LINE = re.compile(r"Device\s+([0-9A-Fa-f:]{17})(?:\s+(.*))?")


class BluetoothError(Exception):
    pass


def _strip_ansi(text: str | None) -> str:
    if not text:
        return ""
    return ANSI_ESCAPE.sub("", text)


def _parse_device_lines(*outputs: Iterable[str]) -> List[dict]:
    devices: Dict[str, dict] = {}
    for output in outputs:
        if not output:
            continue
        for raw_line in output.splitlines():
            line = raw_line.strip()
            match = DEVICE_LINE.search(line)
            if not match:
                continue
            mac = match.group(1).upper()
            name = match.group(2).strip() if match.group(2) else "Unbekannt"
            devices.setdefault(mac, {"mac": mac, "name": name})
    return list(devices.values())


def _raise_on_error(code: int, stdout: str, stderr: str, fallback: str) -> None:
    if code == 0:
        return
    detail = stderr.strip() or stdout.strip() or fallback
    raise BluetoothError(detail)


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
    stdout = _strip_ansi(result.stdout)
    stderr = _strip_ansi(result.stderr)
    return result.returncode, stdout, stderr


def run_bluetoothctl_script(commands: List[str], timeout: int = 30) -> Tuple[int, str, str]:
    script = "\n".join(commands + ["quit"])
    cmd = ["bluetoothctl", "--agent", "NoInputNoOutput"]
    return _run(cmd, input_data=script, timeout=timeout)


def scan_devices(timeout: int = 8) -> dict:
    run_bluetoothctl_script(["power on"], timeout=10)
    code, scan_stdout, scan_stderr = _run(
        ["bluetoothctl", "--agent", "NoInputNoOutput", "--timeout", str(timeout), "scan", "on"],
        timeout=timeout + 3,
    )
    if code != 0:
        raise BluetoothError(scan_stderr.strip() or "Scan fehlgeschlagen")

    devices: Dict[str, dict] = {}
    for dev in _parse_device_lines(scan_stdout, scan_stderr):
        devices[dev["mac"]] = dev

    code, stdout, stderr = _run(["bluetoothctl", "devices"], timeout=10)
    devices_listing = ""
    if code == 0:
        devices_listing = stdout
        for dev in _parse_device_lines(stdout, stderr):
            devices.setdefault(dev["mac"], dev)

    return {
        "devices": list(devices.values()),
        "scan_stdout": scan_stdout,
        "scan_stderr": scan_stderr,
        "devices_stdout": devices_listing,
    }


def list_devices() -> List[dict]:
    code, stdout, stderr = _run(["bluetoothctl", "devices"], timeout=10)
    if code != 0:
        raise BluetoothError(stderr.strip() or "Geraeteliste fehlgeschlagen")
    return _parse_device_lines(stdout, stderr)


def pair_device(mac: str) -> Tuple[int, str, str]:
    script = textwrap.dedent(
        f"""
        power on
        pairable on
        discoverable on
        pair {mac}
        trust {mac}
        """
    )
    code, stdout, stderr = run_bluetoothctl_script(script.strip().splitlines(), timeout=75)
    _raise_on_error(code, stdout, stderr, "Pairing fehlgeschlagen")
    return code, stdout, stderr


def connect_device(mac: str) -> Tuple[int, str, str]:
    script = [
        "power on",
        f"connect {mac}",
    ]
    code, stdout, stderr = run_bluetoothctl_script(script, timeout=40)
    _raise_on_error(code, stdout, stderr, "Connect fehlgeschlagen")
    return code, stdout, stderr


def disconnect_device(mac: str) -> Tuple[int, str, str]:
    script = [
        "power on",
        f"disconnect {mac}",
    ]
    code, stdout, stderr = run_bluetoothctl_script(script, timeout=30)
    _raise_on_error(code, stdout, stderr, "Disconnect fehlgeschlagen")
    return code, stdout, stderr


def remove_device(mac: str) -> Tuple[int, str, str]:
    script = [
        "power on",
        f"remove {mac}",
    ]
    code, stdout, stderr = run_bluetoothctl_script(script, timeout=30)
    _raise_on_error(code, stdout, stderr, "Remove fehlgeschlagen")
    return code, stdout, stderr


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


