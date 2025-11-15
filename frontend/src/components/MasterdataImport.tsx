import { useState } from "react";

interface Props {
  onUpload: (file: File) => Promise<void>;
}

export function MasterdataImport({ onUpload }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setBusy(true);
    try {
      await onUpload(file);
      setFile(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-800 p-4 rounded-md shadow flex flex-col gap-2 text-slate-800 dark:text-slate-100">
      <div className="font-semibold text-slate-800 dark:text-slate-100">Projekte / Milestones via CSV</div>
      <p className="text-sm text-slate-600 dark:text-slate-300">
        Pflicht: <code>project_name</code> oder <code>Projekte</code>. Optional:{" "}
        <code>milestone_name</code> / <code>Arbeitspaket</code>, <code>Sollstunden</code>,{" "}
        <code>Erbrachte Stunden</code>, weitere Felder werden ignoriert.
      </p>
      <div className="flex gap-2 items-center">
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="text-sm text-slate-800 dark:text-slate-100"
        />
        <button
          className="px-4 py-2 rounded bg-emerald-600 text-white disabled:bg-emerald-300"
          disabled={!file || busy}
          onClick={handleUpload}
        >
          {busy ? "Importiert…" : "Import starten"}
        </button>
        {file && (
          <span className="text-sm text-slate-500 dark:text-slate-300">
            {file.name} ({Math.round(file.size / 1024)} KB)
          </span>
        )}
      </div>
    </div>
  );
}
