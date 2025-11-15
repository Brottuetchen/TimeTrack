import { useEffect, useState } from "react";
import toast from "react-hot-toast";

export function LogoSettings() {
  const [logo, setLogo] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const API_BASE = import.meta.env.VITE_API_BASE ||
    `${window.location.protocol}//${window.location.hostname}:8000`;

  useEffect(() => {
    loadLogo();
  }, []);

  const loadLogo = async () => {
    try {
      const response = await fetch(`${API_BASE}/settings/logo`);
      if (response.ok) {
        const data = await response.json();
        setLogo(data.logo_svg || null);
      }
    } catch (err) {
      console.error("Fehler beim Laden des Logos:", err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".svg")) {
      toast.error("Bitte nur SVG-Dateien hochladen");
      return;
    }

    if (file.size > 500 * 1024) {
      toast.error("Logo-Datei zu groß (max. 500 KB)");
      return;
    }

    setUploading(true);
    try {
      const text = await file.text();
      const response = await fetch(`${API_BASE}/settings/logo`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ logo_svg: text }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Logo upload failed:", response.status, errorText);
        throw new Error(`Upload fehlgeschlagen (${response.status}): ${errorText}`);
      }

      setLogo(text);
      toast.success("Logo hochgeladen");

      // Trigger custom event für App.tsx
      window.dispatchEvent(new CustomEvent("logo-updated", { detail: { logo: text } }));
    } catch (err) {
      console.error("Logo upload error:", err);
      toast.error(err instanceof Error ? err.message : "Fehler beim Hochladen");
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveLogo = async () => {
    try {
      const response = await fetch(`${API_BASE}/settings/logo`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Löschen fehlgeschlagen");

      setLogo(null);
      toast.success("Logo entfernt");

      // Trigger custom event für App.tsx
      window.dispatchEvent(new CustomEvent("logo-updated", { detail: { logo: null } }));
    } catch (err) {
      console.error(err);
      toast.error("Fehler beim Löschen");
    }
  };

  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Lade ein SVG-Logo hoch, das neben dem TimeTrack Review Banner angezeigt wird.
      </p>

      <div className="space-y-4">
        {/* Vorschau */}
        {logo && (
          <div className="p-4 border border-slate-200 dark:border-slate-700 rounded bg-slate-50 dark:bg-slate-900">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Vorschau</h3>
            <div className="flex items-center justify-center p-6 bg-white dark:bg-slate-800 rounded">
              <div
                className="max-h-16 max-w-[200px]"
                dangerouslySetInnerHTML={{ __html: logo }}
              />
            </div>
          </div>
        )}

        {/* Upload */}
        <div className="flex gap-3">
          <label
            className={`
              px-4 py-2 rounded cursor-pointer transition-colors
              ${
                uploading
                  ? "bg-slate-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-500 dark:bg-blue-500 dark:hover:bg-blue-400"
              }
              text-white
            `}
          >
            <input
              type="file"
              accept=".svg"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
            {uploading ? "Lädt hoch..." : "SVG hochladen"}
          </label>

          {logo && (
            <button
              onClick={handleRemoveLogo}
              className="px-4 py-2 rounded border border-red-300 dark:border-red-600 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Logo entfernen
            </button>
          )}
        </div>

        {/* Hinweise */}
        <div className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
          <p className="font-medium">ℹ️ Hinweise:</p>
          <ul className="list-disc list-inside space-y-1 pl-2">
            <li>Nur SVG-Dateien erlaubt (max. 500 KB)</li>
            <li>Das Logo wird automatisch auf max. 64px Höhe skaliert</li>
            <li>Dunkle und helle SVGs werden im Dark Mode automatisch angepasst</li>
            <li>Das Logo erscheint links neben "TimeTrack Review"</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
