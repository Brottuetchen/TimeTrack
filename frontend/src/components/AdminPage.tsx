import { useState } from "react";
import { BluetoothSetup } from "./BluetoothSetup";
import { PrivacyControls } from "./PrivacyControls";
import { CallSyncSettings } from "./CallSyncSettings";
import { MasterdataImport } from "./MasterdataImport";

interface Props {
  onMasterdataUpload: (file: File) => Promise<void>;
}

type Tab = "privacy" | "bluetooth" | "callsync" | "import";

export function AdminPage({ onMasterdataUpload }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("privacy");

  const tabs = [
    { id: "privacy" as Tab, label: "Privacy & Filter", icon: "🔒" },
    { id: "bluetooth" as Tab, label: "Bluetooth", icon: "📱" },
    { id: "callsync" as Tab, label: "Call-Sync", icon: "📞" },
    { id: "import" as Tab, label: "Daten-Import", icon: "📥" },
  ];

  return (
    <section className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-hidden">
      {/* Header mit Tab-Navigation */}
      <div className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
        <div className="p-6 pb-0">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">⚙️ Administration</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300 mb-4">
            Konfiguration für Logging, Bluetooth-Geräte, Call-Synchronisation und Daten-Import
          </p>
        </div>

        {/* Tab-Leiste */}
        <div className="flex gap-1 px-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                px-4 py-3 rounded-t-lg font-medium text-sm transition-colors
                ${
                  activeTab === tab.id
                    ? "bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 border-t border-l border-r border-slate-200 dark:border-slate-700"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50"
                }
              `}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab-Content */}
      <div className="p-6">
        {activeTab === "privacy" && <PrivacyControls />}
        {activeTab === "bluetooth" && <BluetoothSetup />}
        {activeTab === "callsync" && <CallSyncSettings />}
        {activeTab === "import" && <MasterdataImport onUpload={onMasterdataUpload} />}
      </div>
    </section>
  );
}
