import { BulkForm, Milestone, Project } from "../types";

interface Props {
  selectedCount: number;
  bulkForm: BulkForm;
  projects: Project[];
  milestones: Milestone[];
  activityOptions: string[];
  onChange: (form: BulkForm) => void;
  onApply: () => void;
  onClear: () => void;
  onMarkPrivate?: () => void;
  onMarkStandard?: () => void;
  onUnassign?: () => void;
  onDelete?: () => void;
}

export function BulkAssignBar({
  selectedCount,
  bulkForm,
  projects,
  milestones,
  activityOptions,
  onChange,
  onApply,
  onClear,
  onMarkPrivate,
  onMarkStandard,
  onUnassign,
  onDelete,
}: Props) {
  return (
    <div className="bg-white dark:bg-slate-800 p-4 rounded-md shadow space-y-3 text-slate-800 dark:text-slate-100">
      {/* Header mit Bulk-Operations */}
      <div className="flex items-center justify-between gap-4">
        <div className="font-semibold text-slate-700 dark:text-slate-100">
          Bulk-Auswahl: {selectedCount} Events
        </div>
        <div className="flex gap-2">
          {onMarkPrivate && (
            <button
              onClick={onMarkPrivate}
              className="px-3 py-1.5 text-sm rounded border border-orange-500 text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20 disabled:opacity-50"
              disabled={!selectedCount}
              title="Markiere ausgewählte Events als privat"
            >
              Als privat
            </button>
          )}
          {onMarkStandard && (
            <button
              onClick={onMarkStandard}
              className="px-3 py-1.5 text-sm rounded border border-green-500 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 disabled:opacity-50"
              disabled={!selectedCount}
              title="Markiere ausgewählte Events als Standard (nicht privat)"
            >
              Als Standard
            </button>
          )}
          {onUnassign && (
            <button
              onClick={onUnassign}
              className="px-3 py-1.5 text-sm rounded border border-yellow-500 text-yellow-600 dark:text-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 disabled:opacity-50"
              disabled={!selectedCount}
              title="Entferne Zuweisungen von ausgewählten Events"
            >
              Zuweisung entfernen
            </button>
          )}
          {onDelete && (
            <button
              onClick={onDelete}
              className="px-3 py-1.5 text-sm rounded border border-red-500 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
              disabled={!selectedCount}
              title="Lösche ausgewählte Events"
            >
              Löschen
            </button>
          )}
        </div>
      </div>

      {/* Bulk-Assign Form */}
      <div className="flex flex-wrap gap-4 items-end">
        <div className="flex flex-col">
        <label className="text-xs font-semibold text-slate-500 dark:text-slate-300">Projekt</label>
        <select
          className="border rounded px-2 py-1 min-w-[180px] bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
          value={bulkForm.project_id || ""}
          onChange={(e) => onChange({ ...bulkForm, project_id: Number(e.target.value) || undefined })}
        >
          <option value="">–</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col">
        <label className="text-xs font-semibold text-slate-500 dark:text-slate-300">Milestone</label>
        <select
          className="border rounded px-2 py-1 min-w-[180px] bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
          value={bulkForm.milestone_id || ""}
          onChange={(e) => onChange({ ...bulkForm, milestone_id: Number(e.target.value) || undefined })}
        >
          <option value="">–</option>
          {milestones
            .filter((m) => !bulkForm.project_id || m.project_id === bulkForm.project_id)
            .map((milestone) => (
              <option key={milestone.id} value={milestone.id}>
                {milestone.name}
              </option>
            ))}
        </select>
      </div>
      <div className="flex flex-col">
        <label className="text-xs font-semibold text-slate-500 dark:text-slate-300">Activity</label>
        <select
          className="border rounded px-2 py-1 bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
          value={bulkForm.activity_type || ""}
          onChange={(e) => onChange({ ...bulkForm, activity_type: e.target.value || undefined })}
        >
          <option value="">–</option>
          {activityOptions.map((activity) => (
            <option key={activity} value={activity}>
              {activity}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col flex-grow min-w-[220px]">
        <label className="text-xs font-semibold text-slate-500 dark:text-slate-300">Kommentar</label>
        <input
          className="border rounded px-2 py-1 bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
          value={bulkForm.comment || ""}
          onChange={(e) => onChange({ ...bulkForm, comment: e.target.value || undefined })}
        />
      </div>
        <div className="ml-auto flex gap-2">
          <button className="px-4 py-2 rounded border border-slate-300 dark:border-slate-600" onClick={onClear}>
            Auswahl leeren
          </button>
          <button
            onClick={onApply}
            className="bg-blue-600 text-white px-4 py-2 rounded disabled:bg-blue-300 dark:disabled:bg-blue-400"
            disabled={!selectedCount || !bulkForm.project_id}
          >
            Zuweisen
          </button>
        </div>
      </div>
    </div>
  );
}
