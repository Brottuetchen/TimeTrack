import { PrivacyControls } from "./PrivacyControls";

export function PrivacyPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <header>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-2">🔒 Privacy Einstellungen</h1>
        <p className="text-slate-600 dark:text-slate-300">
          Konfiguriere Filter-Listen und den Privacy-Modus für das Event-Tracking.
        </p>
      </header>

      {/* Privacy Controls */}
      <section className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6">
        <PrivacyControls />
      </section>

      {/* Info-Boxen */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-2">📝 Whitelist</h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Prozesse auf der Whitelist werden <strong>immer</strong> getrackt, unabhängig von der Blacklist. Nützlich
            für wichtige Arbeits-Tools.
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-2">🚫 Blacklist</h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Prozesse auf der Blacklist werden <strong>nie</strong> getrackt. Ideal für private Anwendungen oder
            Ablenkungen.
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-2">⏸️ Privacy-Modus</h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Pausiert das Tracking komplett für eine bestimmte Dauer. Perfekt für Pausen, private Zeit oder nach
            Feierabend.
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-2">🔄 Sync</h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Änderungen werden automatisch an alle verbundenen Windows Agents verteilt (alle 60 Sekunden).
          </p>
        </div>
      </div>

      {/* Anleitung */}
      <div className="rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 p-4">
        <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">💡 Tipps</h3>
        <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1 list-disc list-inside">
          <li>Prozessnamen müssen exakt geschrieben werden (z.B. "chrome.exe", nicht "Chrome")</li>
          <li>Ein Prozess pro Zeile - keine Kommas oder Semikolons</li>
          <li>Groß-/Kleinschreibung wird ignoriert</li>
          <li>Privacy-Modus "Unbegrenzt" muss manuell beendet werden</li>
          <li>Whitelist hat Vorrang vor Blacklist</li>
        </ul>
      </div>
    </div>
  );
}
