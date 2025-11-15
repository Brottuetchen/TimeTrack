import { useState } from "react";

interface CommandProps {
  label: string;
  command: string;
}

const CommandBlock = ({ label, command }: CommandProps) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-3">
      <div className="flex items-center justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
        {label}
        <button
          onClick={handleCopy}
          className="text-blue-600 dark:text-blue-300 text-xs hover:underline"
        >
          {copied ? "Kopiert" : "Kopieren"}
        </button>
      </div>
      <pre className="mt-2 whitespace-pre-wrap text-[13px] text-slate-800 dark:text-slate-100">{command}</pre>
    </div>
  );
};

export const BluetoothSetup = () => {
  const [mac, setMac] = useState("90:B7:90:3D:03:22");
  const btctlCommands = `sudo bluetoothctl
power on
agent on
default-agent
discoverable on
pairable on
scan on`;

  const pairingCommands = `pair ${mac}
trust ${mac}
connect ${mac}
scan off`;

  const pbapBlock = `sudo -u trapp obexctl <<'EOF'
connect ${mac} PBAP
get telecom/callhistory.vcf /tmp/manual.vcf
quit
EOF`;

  const serviceBlock = `[Service]
Environment=TIMETRACK_PBAP_DEVICE=${mac}
Environment=TIMETRACK_PBAP_STATE=/var/lib/timetrack/pbap_state.json
Environment=TIMETRACK_PBAP_INTERVAL=900`;

  const manualSync = `cd ~/TimeTrack/pi_services/call_logger
source .venv/bin/activate
PYTHONPATH=. python - <<'PY'
from pbap_sync import PBAPSync
import requests, logging
from pathlib import Path

sync = PBAPSync(
    device_mac="${mac}",
    api_base="http://127.0.0.1:8000",
    session=requests.Session(),
    device_id="raspi-pi5",
    user_id="default",
    state_path=Path("/var/lib/timetrack/pbap_state.json"),
    interval_seconds=900,
    logger=logging.getLogger("pbap-manual"),
)
sync.sync_once()
PY`;

  return (
    <section className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 space-y-4">
      <header>
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Bluetooth Setup</h2>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Einmalige Pairing- und PBAP-Schritte für das iPhone. MAC-Adresse bitte anpassen.
        </p>
      </header>
      <div>
        <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">iPhone MAC-Adresse</label>
        <input
          className="mt-1 w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
          value={mac}
          onChange={(e) => setMac(e.target.value)}
          placeholder="AA:BB:CC:DD:EE:FF"
        />
      </div>
      <div className="space-y-3">
        <CommandBlock label="Bluetoothctl Basis" command={btctlCommands} />
        <CommandBlock label="Pairing & Vertrauen" command={pairingCommands} />
        <CommandBlock label="PBAP Download (Test)" command={pbapBlock} />
        <CommandBlock label="Service-Env (timetrack-call-logger)" command={serviceBlock} />
        <CommandBlock label="Manueller PBAP Sync" command={manualSync} />
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Hinweis: Nach Änderungen bitte `sudo systemctl daemon-reload` und `sudo systemctl restart timetrack-call-logger`
        ausführen. Im Journal (`sudo journalctl -u timetrack-call-logger -f`) siehst du Live-/PBAP-Events.
      </p>
    </section>
  );
};
