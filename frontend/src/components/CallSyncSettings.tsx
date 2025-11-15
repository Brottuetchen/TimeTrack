import { useEffect, useState } from "react";
import toast from "react-hot-toast";

interface CallSyncConfig {
  teams_enabled?: boolean;
  teams_tenant_id?: string;
  teams_client_id?: string;
  teams_client_secret?: string;
  placetel_enabled?: boolean;
  placetel_shared_secret?: string;
}

interface CallSyncStatus {
  enabled: boolean;
  teams_enabled: boolean;
  placetel_enabled: boolean;
  interval_minutes: number;
  last_sync_time: string | null;
  last_sync_success: boolean;
  last_sync_error: string | null;
  sync_count: number;
  next_sync_in_seconds: number | null;
}

export function CallSyncSettings() {
  const [config, setConfig] = useState<CallSyncConfig>({});
  const [status, setStatus] = useState<CallSyncStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [showSecrets, setShowSecrets] = useState(false);

  useEffect(() => {
    loadConfig();
    loadStatus();
    // Status alle 30 Sekunden aktualisieren
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadConfig = async () => {
    try {
      const response = await fetch("/api/settings/logging");
      if (!response.ok) throw new Error("Konnte Settings nicht laden");
      const data = await response.json();
      setConfig({
        teams_tenant_id: data.teams_tenant_id || "",
        teams_client_id: data.teams_client_id || "",
        teams_client_secret: data.teams_client_secret || "",
        placetel_shared_secret: data.placetel_shared_secret || "",
      });
    } catch (err) {
      console.error(err);
      toast.error("Fehler beim Laden der Call-Sync-Einstellungen");
    }
  };

  const loadStatus = async () => {
    // TODO: Endpoint für Call-Sync-Status erstellen
    // Für jetzt simulieren wir den Status
    try {
      // Placeholder - in Zukunft könnte der Windows Agent einen Status-Endpoint bereitstellen
      setStatus(null);
    } catch (err) {
      console.error(err);
    }
  };

  const saveConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/settings/logging", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      if (!response.ok) throw new Error("Konnte Settings nicht speichern");
      toast.success("Call-Sync-Einstellungen gespeichert");
      await loadConfig();
    } catch (err) {
      console.error(err);
      toast.error("Fehler beim Speichern");
    } finally {
      setLoading(false);
    }
  };

  const triggerManualSync = async (source: "teams" | "placetel") => {
    try {
      let endpoint = "";
      if (source === "teams") {
        // Zeitfenster: letzte 7 Tage
        const end = new Date().toISOString();
        const start = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
        endpoint = `/api/calls/sync/teams?start=${start}&end=${end}`;
      }

      const response = await fetch(endpoint, { method: "POST" });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Sync fehlgeschlagen");
      }

      toast.success(`${source === "teams" ? "Teams" : "Placetel"}-Sync gestartet`);
      await loadStatus();
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || "Sync fehlgeschlagen");
    }
  };

  const formatTimestamp = (ts: string | null) => {
    if (!ts) return "noch nie";
    try {
      return new Date(ts).toLocaleString("de-DE");
    } catch {
      return "unbekannt";
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "0 min";
    const minutes = Math.floor(seconds / 60);
    return `${minutes} min`;
  };

  return (
    <section className="p-6 rounded-lg bg-white dark:bg-slate-800 shadow space-y-6">
      <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Call-Sync Einstellungen</h2>

      <div className="space-y-6">
        {/* Microsoft Teams */}
        <div className="space-y-3 p-4 border border-slate-200 dark:border-slate-700 rounded">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19.198 5.57A10.45 10.45 0 0 0 12 3C6.477 3 2 7.477 2 13s4.477 10 10 10 10-4.477 10-10c0-2.547-.952-4.877-2.518-6.643l-.284.213z"/>
            </svg>
            Microsoft Teams
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Synchronisiert Anrufe aus Microsoft Teams via Graph API
          </p>

          <div className="grid grid-cols-1 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Tenant ID
              </label>
              <input
                type="text"
                value={config.teams_tenant_id || ""}
                onChange={(e) => setConfig({ ...config, teams_tenant_id: e.target.value })}
                placeholder="00000000-0000-0000-0000-000000000000"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Client ID
              </label>
              <input
                type="text"
                value={config.teams_client_id || ""}
                onChange={(e) => setConfig({ ...config, teams_client_id: e.target.value })}
                placeholder="00000000-0000-0000-0000-000000000000"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Client Secret
              </label>
              <div className="flex gap-2">
                <input
                  type={showSecrets ? "text" : "password"}
                  value={config.teams_client_secret || ""}
                  onChange={(e) => setConfig({ ...config, teams_client_secret: e.target.value })}
                  placeholder="*********************"
                  className="flex-1 px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                />
                <button
                  onClick={() => setShowSecrets(!showSecrets)}
                  className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded hover:bg-slate-100 dark:hover:bg-slate-700"
                  title={showSecrets ? "Secrets verbergen" : "Secrets anzeigen"}
                >
                  {showSecrets ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            <button
              onClick={() => triggerManualSync("teams")}
              disabled={!config.teams_tenant_id || !config.teams_client_id || !config.teams_client_secret}
              className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-500 disabled:bg-slate-400 disabled:cursor-not-allowed dark:bg-blue-500 dark:hover:bg-blue-400"
            >
              Teams-Sync manuell starten (letzte 7 Tage)
            </button>
          </div>
        </div>

        {/* Placetel */}
        <div className="space-y-3 p-4 border border-slate-200 dark:border-slate-700 rounded">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1C10.74 21 3 13.26 3 4c0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/>
            </svg>
            Placetel
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Empfängt Anrufe via Webhook (Echtzeit)
          </p>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Shared Secret (für Webhook-Signatur)
            </label>
            <input
              type={showSecrets ? "text" : "password"}
              value={config.placetel_shared_secret || ""}
              onChange={(e) => setConfig({ ...config, placetel_shared_secret: e.target.value })}
              placeholder="*********************"
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
            />
          </div>

          <div className="text-sm text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 p-3 rounded">
            <strong>Webhook-URL:</strong>{" "}
            <code className="bg-slate-200 dark:bg-slate-800 px-2 py-1 rounded">
              {window.location.origin}/api/calls/webhooks/placetel
            </code>
          </div>
        </div>

        {/* Status Anzeige */}
        {status && (
          <div className="space-y-3 p-4 border border-slate-200 dark:border-slate-700 rounded bg-slate-50 dark:bg-slate-900">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Sync-Status</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-slate-600 dark:text-slate-400">Letzter Sync:</span>
                <p className="font-medium">{formatTimestamp(status.last_sync_time)}</p>
              </div>
              <div>
                <span className="text-slate-600 dark:text-slate-400">Status:</span>
                <p className="font-medium">
                  {status.last_sync_success ? (
                    <span className="text-green-600 dark:text-green-400">✓ Erfolgreich</span>
                  ) : (
                    <span className="text-red-600 dark:text-red-400">✗ Fehler</span>
                  )}
                </p>
              </div>
              <div>
                <span className="text-slate-600 dark:text-slate-400">Anzahl Syncs:</span>
                <p className="font-medium">{status.sync_count}</p>
              </div>
              <div>
                <span className="text-slate-600 dark:text-slate-400">Nächster Sync in:</span>
                <p className="font-medium">{formatDuration(status.next_sync_in_seconds)}</p>
              </div>
            </div>
            {status.last_sync_error && (
              <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded">
                <strong>Fehler:</strong> {status.last_sync_error}
              </div>
            )}
          </div>
        )}

        {/* Speichern-Button */}
        <div className="flex gap-3">
          <button
            onClick={saveConfig}
            disabled={loading}
            className="px-6 py-2 rounded bg-green-600 text-white hover:bg-green-500 disabled:bg-slate-400 dark:bg-green-500 dark:hover:bg-green-400"
          >
            {loading ? "Speichert..." : "Einstellungen speichern"}
          </button>
          <button
            onClick={loadConfig}
            className="px-4 py-2 rounded border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            Zurücksetzen
          </button>
        </div>

        {/* Hinweise */}
        <div className="text-sm text-slate-600 dark:text-slate-400 space-y-2">
          <p className="font-medium">ℹ️ Hinweise:</p>
          <ul className="list-disc list-inside space-y-1 pl-2">
            <li>Der Call-Sync wird vom Windows Agent ausgeführt (alle 15 min)</li>
            <li>Teams benötigt eine Azure AD App-Registrierung mit CallRecords.Read.All Permission</li>
            <li>Placetel-Webhook muss in den Placetel-Einstellungen konfiguriert werden</li>
            <li>Credentials werden im Backend gespeichert (logging_settings.json)</li>
          </ul>
        </div>
      </div>
    </section>
  );
}
