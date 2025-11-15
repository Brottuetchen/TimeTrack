import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import {
  allowIncomingPair,
  connectBluetooth,
  disconnectBluetooth,
  fetchIncomingPairingStatus,
  listBluetoothDevices,
  pairBluetooth,
  removeBluetooth,
  scanBluetooth,
  triggerPbap,
} from "../api";
import type { BluetoothCommandResult } from "../api";

interface BluetoothDevice {
  mac: string;
  name: string;
}

export const BluetoothSetup = () => {
  const [mac, setMac] = useState("");
  const [devices, setDevices] = useState<BluetoothDevice[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [incomingDuration, setIncomingDuration] = useState(60);
  const [incomingStatus, setIncomingStatus] = useState<{ active: boolean; mac?: string; expires_at?: number }>({
    active: false,
  });

  const appendLog = (message: string) => {
    setLogs((prev) => [...prev.slice(-25), `${new Date().toLocaleTimeString()} ${message}`]);
  };

  const logCommandResult = (result?: { stdout?: string; stderr?: string }) => {
    if (!result) return;
    const logText = (label: string, value?: string) => {
      if (!value) return;
      value
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .forEach((line) => appendLog(`${label}: ${line}`));
    };
    logText("stdout", result.stdout);
    logText("stderr", result.stderr);
  };

  const loadDevices = async () => {
    try {
      const list = await listBluetoothDevices();
      setDevices(list);
      appendLog(`Geraete geladen (${list.length})`);
    } catch (err) {
      console.error(err);
      toast.error("Geraete konnten nicht geladen werden");
    }
  };

  const loadIncomingStatus = async () => {
    try {
      const status = await fetchIncomingPairingStatus();
      setIncomingStatus(status);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadDevices();
    loadIncomingStatus();
  }, []);

  const handleScan = async () => {
    setLoading(true);
    try {
      const response = await scanBluetooth();
      setDevices(response.devices);
      appendLog(`Scan abgeschlossen (${response.devices.length} Geraete)`);
      logCommandResult({ stdout: response.scan_stdout, stderr: response.scan_stderr });
      logCommandResult({ stdout: response.devices_stdout });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Scan fehlgeschlagen");
      appendLog("Scan fehlgeschlagen");
    } finally {
      setLoading(false);
    }
  };

  const resolveMac = (target?: string) => {
    const value = target ?? mac;
    if (!value) {
      toast.error("Bitte MAC-Adresse auswaehlen");
      return undefined;
    }
    return value;
  };

  const runAction = async (
    action: (macAddress: string) => Promise<BluetoothCommandResult>,
    successMessage: (macAddress: string) => string,
    target?: string,
    postAction?: () => Promise<void> | void
  ) => {
    const macAddress = resolveMac(target);
    if (!macAddress) return;
    try {
      const result = await action(macAddress);
      const message = successMessage(macAddress);
      toast.success(message);
      appendLog(message);
      logCommandResult(result);
      if (postAction) {
        await postAction();
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "Aktion fehlgeschlagen";
      toast.error(detail);
      appendLog(detail);
    }
  };

  const handlePbap = async () => {
    const macAddress = resolveMac();
    if (!macAddress) return;
    try {
      const result = await triggerPbap(macAddress);
      const bytes = result?.bytes ?? 0;
      const path = result?.path ?? "unbekannt";
      const message = `PBAP Sync fuer ${macAddress} (${bytes} Bytes)`;
      toast.success(message);
      appendLog(`${message} -> ${path}`);
      logCommandResult(result);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "PBAP Sync fehlgeschlagen";
      toast.error(detail);
      appendLog(detail);
    }
  };

  const handleIncomingPairing = async () => {
    const macAddress = resolveMac();
    if (!macAddress) return;
    try {
      const result = await allowIncomingPair(macAddress, incomingDuration);
      const expires = result?.expires_at ? new Date(result.expires_at * 1000) : null;
      const message = `Auto-Accept aktiviert fuer ${macAddress} (${incomingDuration}s)`;
      toast.success(message);
      appendLog(expires ? `${message} -> bis ${expires.toLocaleTimeString()}` : message);
      await loadIncomingStatus();
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "Pairing-Freigabe fehlgeschlagen";
      toast.error(detail);
      appendLog(detail);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600 dark:text-slate-300">
        Geräte scannen, pairen, verbinden und PBAP-Sync direkt im Browser.
      </p>

      <div className="flex flex-col gap-2 md:flex-row md:items-end">
        <div className="flex-1">
          <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">MAC-Adresse</label>
          <input
            className="mt-1 w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
            value={mac}
            onChange={(e) => setMac(e.target.value)}
            placeholder="AA:BB:CC:DD:EE:FF"
          />
        </div>
        <button
          onClick={handleScan}
          className="rounded bg-blue-600 text-white px-4 py-2 text-sm hover:bg-blue-500 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Scanne..." : "Scan starten"}
        </button>
        <button
          onClick={loadDevices}
          className="rounded border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-700"
        >
          Liste aktualisieren
        </button>
      </div>

      <div className="overflow-auto rounded border border-slate-200 dark:border-slate-700">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100 dark:bg-slate-700 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-200">
            <tr>
              <th className="px-2 py-2">MAC</th>
              <th className="px-2 py-2">Name</th>
              <th className="px-2 py-2 w-44">Aktionen</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((device) => (
              <tr
                key={device.mac}
                className={`border-t border-slate-200 dark:border-slate-700 cursor-pointer ${
                  mac === device.mac ? "bg-blue-50 dark:bg-blue-900/30" : ""
                }`}
                onClick={() => setMac(device.mac)}
              >
                <td className="px-2 py-2 font-mono text-xs">{device.mac}</td>
                <td className="px-2 py-2">{device.name}</td>
                <td className="px-2 py-2 space-x-2">
                  <button
                    className="text-xs text-blue-600 hover:underline"
                    onClick={() => runAction(pairBluetooth, (value) => `Pairing/Trust fuer ${value}`, device.mac)}
                  >
                    Pair
                  </button>
                  <button
                    className="text-xs text-green-600 hover:underline"
                    onClick={() => runAction(connectBluetooth, (value) => `Verbunden mit ${value}`, device.mac)}
                  >
                    Connect
                  </button>
                  <button
                    className="text-xs text-red-600 hover:underline"
                    onClick={() =>
                      runAction(disconnectBluetooth, (value) => `Verbindung getrennt (${value})`, device.mac)
                    }
                  >
                    Disconnect
                  </button>
                  <button
                    className="text-xs text-amber-600 hover:underline"
                    onClick={(event) => {
                      event.stopPropagation();
                      runAction(
                        removeBluetooth,
                        (value) => `Geraet entfernt (${value})`,
                        device.mac,
                        loadDevices
                      );
                    }}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
            {!devices.length && (
              <tr>
                <td className="px-2 py-4 text-center text-slate-500 dark:text-slate-400" colSpan={3}>
                  Keine Geraete gefunden - bitte Scan ausfuehren.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="rounded border border-slate-200 dark:border-slate-700 p-4 space-y-2">
        <p className="text-sm text-slate-700 dark:text-slate-200 font-semibold">iPhone-Pairing Freigabe</p>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Aktiviert den Pi fuer eingehende Pairing-Anfragen fuer ein bestimmtes Geraet. Nach Ablauf wird die Freigabe
          automatisch deaktiviert.
        </p>
        <div className="flex flex-col gap-2 md:flex-row md:items-end">
          <div>
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">Dauer (Sekunden)</label>
            <input
              type="number"
              min={5}
              max={300}
              value={incomingDuration}
              onChange={(e) => setIncomingDuration(Number(e.target.value))}
              className="mt-1 w-32 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-3 py-2 text-sm"
            />
          </div>
          <button
            onClick={handleIncomingPairing}
            className="rounded bg-purple-600 text-white px-4 py-2 text-sm hover:bg-purple-500"
          >
            Freigabe starten
          </button>
          <div className="text-xs text-slate-600 dark:text-slate-300">
            {incomingStatus.active && incomingStatus.expires_at ? (
              <span>
                Aktiv fuer {incomingStatus.mac} bis{" "}
                {new Date(incomingStatus.expires_at * 1000).toLocaleTimeString()}
              </span>
            ) : (
              <span>Keine aktive Freigabe</span>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => runAction(pairBluetooth, (value) => `Pairing/Trust fuer ${value}`)}
          className="rounded border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-700"
        >
          Pair + Trust
        </button>
        <button
          onClick={() => runAction(connectBluetooth, (value) => `Verbunden mit ${value}`)}
          className="rounded border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-700"
        >
          Verbinden
        </button>
        <button
          onClick={() => runAction(disconnectBluetooth, (value) => `Verbindung getrennt (${value})`)}
          className="rounded border border-slate-300 dark:border-slate-600 px-4 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-700"
        >
          Trennen
        </button>
        <button
          onClick={() => runAction(removeBluetooth, (value) => `Geraet entfernt (${value})`, undefined, loadDevices)}
          className="rounded border border-amber-500 text-amber-700 dark:text-amber-300 px-4 py-2 text-sm hover:bg-amber-50 dark:hover:bg-amber-900/40"
        >
          Verbindung entfernen
        </button>
        <button
          onClick={handlePbap}
          className="rounded bg-emerald-600 text-white px-4 py-2 text-sm hover:bg-emerald-500"
        >
          PBAP Sync
        </button>
      </div>

      <div className="rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/40 p-3 max-h-48 overflow-auto text-xs font-mono text-slate-600 dark:text-slate-300">
        {logs.length === 0 ? <p>Noch keine Aktionen.</p> : logs.map((entry, idx) => <div key={idx}>{entry}</div>)}
      </div>
    </div>
  );
};
