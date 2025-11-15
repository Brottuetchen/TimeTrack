import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { activatePrivacyMode, clearPrivacyMode, fetchLoggingSettings, saveLoggingSettings } from "../api";
import { LoggingSettings } from "../types";

const durationOptions = [
  { label: "15 Minuten", value: 15 },
  { label: "30 Minuten", value: 30 },
  { label: "Unbegrenzt", value: 0 },
];

export const PrivacyControls = () => {
  const [settings, setSettings] = useState<LoggingSettings | null>(null);
  const [whitelist, setWhitelist] = useState("");
  const [blacklist, setBlacklist] = useState("");
  const [saving, setSaving] = useState(false);
  const [privacyStatus, setPrivacyStatus] = useState<string>("–");

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await fetchLoggingSettings();
      setSettings(data);
      setWhitelist(data.whitelist.join("\n"));
      setBlacklist(data.blacklist.join("\n"));
      setPrivacyStatus(formatPrivacyStatus(data.privacy_mode_until));
    } catch (err) {
      console.error(err);
      toast.error("Konnte Logging-Settings nicht laden");
    }
  };

  const formatPrivacyStatus = (until: string | null) => {
    if (!until) return "Aktiv";
    if (until.toLowerCase() === "indefinite") return "Pausiert (unbegrenzt)";
    return `Pausiert bis ${new Date(until).toLocaleString()}`;
  };

  const handleSaveLists = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      const payload = {
        whitelist: whitelist
          .split("\n")
          .map((item) => item.trim())
          .filter(Boolean),
        blacklist: blacklist
          .split("\n")
          .map((item) => item.trim())
          .filter(Boolean),
      };
      const updated = await saveLoggingSettings(payload);
      setSettings(updated);
      toast.success("Listen gespeichert");
    } catch (err) {
      console.error(err);
      toast.error("Speichern fehlgeschlagen");
    } finally {
      setSaving(false);
    }
  };

  const handlePrivacy = async (minutes?: number) => {
    try {
      const updated = minutes ? await activatePrivacyMode(minutes) : await activatePrivacyMode();
      setSettings(updated);
      setPrivacyStatus(formatPrivacyStatus(updated.privacy_mode_until));
      toast.success("Privacy-Modus aktualisiert");
    } catch (err) {
      console.error(err);
      toast.error("Privacy-Modus fehlgeschlagen");
    }
  };

  const handleClearPrivacy = async () => {
    try {
      const updated = await clearPrivacyMode();
      setSettings(updated);
      setPrivacyStatus("Aktiv");
      toast.success("Privacy-Modus beendet");
    } catch (err) {
      console.error(err);
      toast.error("Konnte Privacy-Modus nicht beenden");
    }
  };

  if (!settings) {
    return (
      <section className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6">
        <p className="text-sm text-slate-500">Lade Logging-Settings…</p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 space-y-4">
      <header>
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Privacy &amp; Filter</h2>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Whitelist/Blacklist für Prozesse sowie Privacy-Modus (Logging pausieren).
        </p>
      </header>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="flex flex-col">
          <label className="text-xs font-semibold text-slate-500 dark:text-slate-300">Whitelist (ein Prozess pro Zeile)</label>
          <textarea
            className="mt-1 min-h-[120px] rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
            value={whitelist}
            onChange={(e) => setWhitelist(e.target.value)}
            placeholder="acad.exe"
          />
        </div>
        <div className="flex flex-col">
          <label className="text-xs font-semibold text-slate-500 dark:text-slate-300">Blacklist (ein Prozess pro Zeile)</label>
          <textarea
            className="mt-1 min-h-[120px] rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 px-3 py-2 text-sm text-slate-900 dark:text-slate-100"
            value={blacklist}
            onChange={(e) => setBlacklist(e.target.value)}
            placeholder="chrome.exe"
          />
        </div>
      </div>
      <button
        onClick={handleSaveLists}
        disabled={saving}
        className="rounded bg-blue-600 text-white px-4 py-2 text-sm hover:bg-blue-500 disabled:opacity-50"
      >
        {saving ? "Speichere…" : "Listen speichern"}
      </button>
      <div className="border-t border-slate-200 dark:border-slate-700 pt-4 flex flex-col gap-3">
        <div className="text-sm text-slate-600 dark:text-slate-300">Privacy-Modus: {privacyStatus}</div>
        <div className="flex flex-wrap gap-2">
          {durationOptions.map((option) => (
            <button
              key={option.label}
              onClick={() => handlePrivacy(option.value || undefined)}
              className="rounded border border-slate-300 dark:border-slate-600 px-3 py-1 text-sm hover:bg-slate-100 dark:hover:bg-slate-700"
            >
              {option.label}
            </button>
          ))}
          <button
            onClick={handleClearPrivacy}
            className="rounded border border-slate-300 dark:border-slate-600 px-3 py-1 text-sm hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            Privacy beenden
          </button>
        </div>
      </div>
    </section>
  );
};
