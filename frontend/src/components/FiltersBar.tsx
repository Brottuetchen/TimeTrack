import dayjs from "dayjs";
import { Filters, SourceType } from "../types";

interface Props {
  filters: Filters;
  onChange: (filters: Filters) => void;
  onRefresh: () => void;
}

const sourceOptions: { label: string; value: Filters["source"] }[] = [
  { label: "Alle Quellen", value: "all" },
  { label: "Telefon", value: "phone" },
  { label: "Fenster", value: "window" },
];

export function FiltersBar({ filters, onChange, onRefresh }: Props) {
  const handleDate = (key: "start" | "end", value: string) => {
    const iso = value ? dayjs(value).toISOString() : "";
    onChange({ ...filters, [key]: iso });
  };

  return (
    <div className="flex flex-wrap gap-4 items-end bg-white dark:bg-slate-800 p-4 rounded-md shadow text-slate-800 dark:text-slate-100">
      <div className="flex flex-col">
        <label className="text-xs font-semibold text-slate-500 dark:text-slate-300">Start</label>
        <input
          type="datetime-local"
          value={filters.start ? dayjs(filters.start).format("YYYY-MM-DDTHH:mm") : ""}
          onChange={(e) => handleDate("start", e.target.value)}
          className="border rounded px-2 py-1 bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
        />
      </div>
      <div className="flex flex-col">
        <label className="text-xs font-semibold text-slate-500 dark:text-slate-300">Ende</label>
        <input
          type="datetime-local"
          value={filters.end ? dayjs(filters.end).format("YYYY-MM-DDTHH:mm") : ""}
          onChange={(e) => handleDate("end", e.target.value)}
          className="border rounded px-2 py-1 bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
        />
      </div>
      <div className="flex flex-col">
        <label className="text-xs font-semibold text-slate-500 dark:text-slate-300">Quelle</label>
        <select
          className="border rounded px-2 py-1 bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
          value={filters.source}
          onChange={(e) => onChange({ ...filters, source: e.target.value as Filters["source"] })}
        >
          {sourceOptions.map((opt) => (
            <option key={opt.value} value={opt.value || "all"}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col">
        <label className="text-xs font-semibold text-slate-500 dark:text-slate-300">User</label>
        <input
          className="border rounded px-2 py-1 bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
          value={filters.user}
          onChange={(e) => onChange({ ...filters, user: e.target.value })}
          placeholder="optional"
        />
      </div>
      <button
        onClick={onRefresh}
        className="ml-auto bg-slate-900 text-white px-4 py-2 rounded hover:bg-slate-800 dark:bg-slate-200 dark:text-slate-900 dark:hover:bg-slate-100"
      >
        Aktualisieren
      </button>
    </div>
  );
}
