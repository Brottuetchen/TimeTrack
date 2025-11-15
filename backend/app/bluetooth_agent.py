import asyncio
import logging
import threading
import time
from typing import Optional

from dbus_fast import BusType, DBusError
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method

from .bluetooth import run_bluetoothctl_script


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("bluetooth-agent")
LOGGER.setLevel(logging.INFO)


class RejectError(DBusError):
    _dbus_error_name = "org.bluez.Error.Rejected"


def _normalize_mac(mac: str) -> str:
    return mac.strip().upper()


def _path_suffix(mac: str) -> str:
    return _normalize_mac(mac).replace(":", "_")


class AutoAcceptAgent(ServiceInterface):
    """BlueZ Agent that auto accepts pairing for a single device."""

    def __init__(self) -> None:
        super().__init__("org.bluez.Agent1")
        self._lock = threading.Lock()
        self._allowed_mac: Optional[str] = None
        self._expires_at: float = 0

    def allow(self, mac: str, ttl: int) -> float:
        expires_at = time.time() + ttl
        with self._lock:
            self._allowed_mac = _normalize_mac(mac)
            self._expires_at = expires_at
        LOGGER.info("Auto-accept enabled for %s until %s", mac, expires_at)
        return expires_at

    def clear(self) -> None:
        with self._lock:
            self._allowed_mac = None
            self._expires_at = 0

    def status(self) -> tuple[Optional[str], float]:
        with self._lock:
            return self._allowed_mac, self._expires_at

    def _is_allowed(self, device_path: str) -> bool:
        with self._lock:
            if not self._allowed_mac or time.time() > self._expires_at:
                return False
            suffix = _path_suffix(self._allowed_mac)
        return device_path.endswith(suffix)

    def _ensure_allowed(self, device_path: str) -> None:
        if not self._is_allowed(device_path):
            LOGGER.warning("Rejecting pairing for %s", device_path)
            raise RejectError("Device not authorized")

    @method()
    def Release(self) -> None:  # pragma: no cover - required by interface
        LOGGER.info("Agent released by BlueZ")
        self.clear()

    @method()
    def Cancel(self) -> None:  # pragma: no cover - required by interface
        LOGGER.info("Agent request canceled")

    @method()
    def RequestPinCode(self, device: "o") -> "s":
        self._ensure_allowed(device)
        return ""

    @method()
    def RequestPasskey(self, device: "o") -> "u":
        self._ensure_allowed(device)
        return 0

    @method()
    def RequestConfirmation(self, device: "o", passkey: "u") -> None:
        self._ensure_allowed(device)

    @method()
    def RequestAuthorization(self, device: "o") -> None:
        self._ensure_allowed(device)

    @method()
    def AuthorizeService(self, device: "o", uuid: "s") -> None:
        self._ensure_allowed(device)

    @method()
    def DisplayPinCode(self, device: "o", pincode: "s") -> None:
        LOGGER.info("DisplayPinCode for %s: %s", device, pincode)

    @method()
    def DisplayPasskey(self, device: "o", passkey: "u", entered: "q") -> None:
        LOGGER.info("DisplayPasskey for %s: %s (%s)", device, passkey, entered)


class AgentController:
    """Controller that keeps DBus agent alive and manages pairing windows."""

    def __init__(self) -> None:
        self._agent = AutoAcceptAgent()
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._bus: Optional[MessageBus] = None
        self._pairing_timer: Optional[threading.Timer] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _runner() -> None:
            asyncio.run(self._run())

        self._thread = threading.Thread(target=_runner, name="bluetooth-agent", daemon=True)
        self._thread.start()
        started = self._ready.wait(timeout=5)
        if not started:
            LOGGER.warning("Bluetooth agent thread did not signal ready state")

    async def _run(self) -> None:
        self._loop = asyncio.get_running_loop()
        try:
            bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
            self._bus = bus
            bus.export("/org/timetrack/agent", self._agent)
            introspection = await bus.introspect("org.bluez", "/org/bluez")
            manager = bus.get_proxy_object("org.bluez", "/org/bluez", introspection)
            agent_manager = manager.get_interface("org.bluez.AgentManager1")
            await agent_manager.call_register_agent("/org/timetrack/agent", "NoInputNoOutput")
            await agent_manager.call_request_default_agent("/org/timetrack/agent")
            LOGGER.info("Bluetooth agent registered")
            self._ready.set()
            await asyncio.Future()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Failed to register bluetooth agent: %s", exc)
            self._ready.set()

    def allow_incoming(self, mac: str, duration: int) -> float:
        self.start()
        expires_at = self._agent.allow(mac, duration)
        self._set_pairable(True)
        if self._pairing_timer:
            self._pairing_timer.cancel()
        self._pairing_timer = threading.Timer(duration, self._disable_pairing_window)
        self._pairing_timer.daemon = True
        self._pairing_timer.start()
        return expires_at

    def _set_pairable(self, enabled: bool) -> None:
        commands = [
            "power on",
            "pairable on" if enabled else "pairable off",
            "discoverable on" if enabled else "discoverable off",
        ]
        try:
            run_bluetoothctl_script(commands, timeout=30)
        except Exception as exc:  # pragma: no cover - best-effort
            LOGGER.error("Failed to toggle pairing mode: %s", exc)

    def _disable_pairing_window(self) -> None:
        self._agent.clear()
        self._set_pairable(False)
        LOGGER.info("Pairing window closed")

    def status(self) -> dict:
        mac, expires = self._agent.status()
        if not mac or time.time() > expires:
            return {"active": False}
        return {"active": True, "mac": mac, "expires_at": expires}


controller = AgentController()


def start_agent() -> None:
    controller.start()


def allow_incoming_pair(mac: str, duration: int = 60) -> float:
    return controller.allow_incoming(mac, duration)


def incoming_status() -> dict:
    return controller.status()
