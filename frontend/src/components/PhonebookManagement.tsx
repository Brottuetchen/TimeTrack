import { useEffect, useState } from "react";
import toast from "react-hot-toast";

interface PhonebookEntry {
  id: number;
  name: string;
  number: string;
  company: string | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
}

export function PhonebookManagement() {
  const [entries, setEntries] = useState<PhonebookEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const API_BASE = import.meta.env.VITE_API_BASE ||
    `${window.location.protocol}//${window.location.hostname}:8000`;

  useEffect(() => {
    loadEntries();
  }, []);

  const loadEntries = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      params.set("limit", "100");

      const response = await fetch(`${API_BASE}/phonebook?${params.toString()}`);
      if (!response.ok) throw new Error("Laden fehlgeschlagen");
      const data = await response.json();
      setEntries(data);
    } catch (err) {
      console.error(err);
      toast.error("Fehler beim Laden des Telefonbuchs");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadEntries();
  };

  const exportCSV = () => {
    const url = `${API_BASE}/phonebook/export/csv`;
    window.open(url, "_blank");
    toast.success("CSV-Export gestartet");
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/phonebook/import/csv`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Import fehlgeschlagen");

      const result = await response.json();
      toast.success(
        `Import erfolgreich: ${result.created_count} neu, ${result.updated_count} aktualisiert`
      );
      loadEntries();
    } catch (err) {
      console.error(err);
      toast.error("CSV-Import fehlgeschlagen");
    }

    // Reset file input
    event.target.value = "";
  };

  if (loading) {
    return <div className="p-6 text-center text-slate-500 dark:text-slate-400">Lädt...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
          Telefonbuch-Management
        </h3>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Verwalte Kontakte für automatische Namensauflösung bei Anrufen.
        </p>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-4 items-center">
        <div className="flex-grow max-w-md">
          <input
            type="text"
            placeholder="Suche nach Name, Nummer oder Firma..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
          />
        </div>
        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Suchen
        </button>
        <button
          onClick={exportCSV}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
        >
          CSV exportieren
        </button>
        <label className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors cursor-pointer">
          CSV importieren
          <input
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            className="hidden"
          />
        </label>
      </div>

      {/* Entries Table */}
      {entries.length === 0 ? (
        <div className="text-center py-12 text-slate-500 dark:text-slate-400">
          {search ? "Keine Treffer gefunden" : "Keine Einträge vorhanden"}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
                <th className="text-left p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Name
                </th>
                <th className="text-left p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Nummer
                </th>
                <th className="text-left p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Firma
                </th>
                <th className="text-left p-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Tags
                </th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr
                  key={entry.id}
                  className="border-b border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                >
                  <td className="p-3 text-sm font-medium text-slate-900 dark:text-slate-100">
                    {entry.name}
                  </td>
                  <td className="p-3 text-sm text-slate-600 dark:text-slate-400">
                    {entry.number}
                  </td>
                  <td className="p-3 text-sm text-slate-600 dark:text-slate-400">
                    {entry.company || "–"}
                  </td>
                  <td className="p-3 text-sm">
                    {entry.tags && entry.tags.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {entry.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-slate-400 dark:text-slate-500">–</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Info Box */}
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <p className="text-sm text-blue-900 dark:text-blue-200">
          <strong>CSV-Format:</strong> name,number,company,tags
          <br />
          <strong>Beispiel:</strong> Max Mustermann,+49123456789,ACME GmbH,"kunde,wichtig"
          <br />
          <strong>Hinweis:</strong> Import aktualisiert bestehende Einträge (gleiche Nummer).
        </p>
      </div>
    </div>
  );
}
