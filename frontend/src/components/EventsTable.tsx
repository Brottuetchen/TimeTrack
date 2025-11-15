import dayjs from "dayjs";
import { Assignment, Event, Milestone, Project } from "../types";
import clsx from "clsx";

interface Props {
  events: Event[];
  assignments: Record<number, Assignment | undefined>;
  projects: Project[];
  milestones: Milestone[];
  selectedIds: Set<number>;
  activityOptions: string[];
  getDefaultActivity: (event: Event) => string;
  getDefaultComment: (event: Event) => string;
  onSelect: (eventId: number, checked: boolean) => void;
  onAssign: (eventId: number, payload: { project_id?: number; milestone_id?: number; activity_type?: string; comment?: string }) => void;
  onPrivacyChange: (eventId: number, isPrivate: boolean) => void;
}

export function EventsTable({
  events,
  assignments,
  projects,
  milestones,
  selectedIds,
  activityOptions,
  getDefaultActivity,
  getDefaultComment,
  onSelect,
  onAssign,
  onPrivacyChange,
}: Props) {
  const milestoneOptions = (projectId?: number) => milestones.filter((m) => !projectId || m.project_id === projectId);
  const columnWidths = {
    time: "8rem",
    source: "5rem",
    details: "16rem",
    select: "11rem",
  };

  const handleProjectChange = (eventObj: Event, projectId?: number) => {
    if (!projectId) {
      onAssign(eventObj.id, { project_id: undefined });
      return;
    }
    onAssign(eventObj.id, { project_id: projectId, milestone_id: undefined });
  };

  return (
    <div className="overflow-x-hidden rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
      <table className="w-full text-sm table-auto">
        <thead className="bg-slate-100 dark:bg-slate-700 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-200">
          <tr>
            <th className="px-2 py-3 w-10 text-center">
              <input
                type="checkbox"
                onChange={(e) => {
                  const checked = e.target.checked;
                  events.forEach((event) => onSelect(event.id, checked));
                }}
              />
            </th>
            <th className="px-2 py-3" style={{ width: columnWidths.time }}>
              Zeit
            </th>
            <th className="px-2 py-3" style={{ width: columnWidths.source }}>
              Quelle
            </th>
            <th className="px-2 py-3" style={{ width: columnWidths.details }}>
              Details
            </th>
            <th className="px-2 py-3" style={{ width: columnWidths.select }}>
              Projekt
            </th>
            <th className="px-2 py-3" style={{ width: columnWidths.select }}>
              Milestone
            </th>
            <th className="px-2 py-3" style={{ width: columnWidths.select }}>
              Activity
            </th>
            <th className="px-2 py-3" style={{ width: columnWidths.select }}>
              Privat
            </th>
            <th className="px-2 py-3">Kommentar</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => {
            const assignment = assignments[event.id];
            const durationMin = event.duration_seconds ? Math.round(event.duration_seconds / 60) : "-";
            const projectId = assignment?.project?.id;
            const milestoneId = assignment?.milestone?.id;
            return (
              <tr
                key={event.id}
                className={clsx(
                  "border-b border-slate-200 dark:border-slate-700 last:border-b-0 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-100",
                  event.is_private && "opacity-60",
                )}
              >
                <td className="px-2 py-3 align-top w-10 text-center">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(event.id)}
                    onChange={(e) => onSelect(event.id, e.target.checked)}
                  />
                </td>
                <td className="px-2 py-3 align-top" style={{ width: columnWidths.time }}>
                  <div className="font-semibold text-slate-800 dark:text-slate-100">
                    {dayjs(event.timestamp_start).format("DD.MM HH:mm")}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-300">
                    Ende {event.timestamp_end ? dayjs(event.timestamp_end).format("HH:mm") : "laufend"}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-300">{durationMin} min</div>
                </td>
                <td className="px-2 py-3 align-top" style={{ width: columnWidths.source }}>
                  <span
                    className={clsx(
                      "rounded px-2 py-1 text-xs font-semibold",
                      event.source_type === "phone"
                        ? "bg-amber-100 text-amber-800 dark:bg-amber-300 dark:text-amber-900"
                        : "bg-sky-100 text-sky-800 dark:bg-sky-300 dark:text-sky-900",
                    )}
                  >
                    {event.source_type === "phone" ? "Telefon" : "Fenster"}
                  </span>
                </td>
                <td className="px-2 py-3 align-top text-xs text-slate-700 break-words" style={{ width: columnWidths.details }}>
                  {event.source_type === "phone" ? (
                    <>
                      <div>{event.contact_name || "Unbekannt"}</div>
                      <div>{event.phone_number}</div>
                      <div>{event.direction}</div>
                    </>
                  ) : (
                    <>
                      <div className="font-semibold">{event.window_title}</div>
                      <div>{event.process_name}</div>
                    </>
                  )}
                </td>
                <td className="px-2 py-3 align-top" style={{ width: columnWidths.select }}>
                  <select
                    className="border rounded px-2 py-1 text-sm w-full bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
                    value={projectId || ""}
                    onChange={(e) => handleProjectChange(event, e.target.value ? Number(e.target.value) : undefined)}
                  >
                    <option value="">– auswählen –</option>
                    {projects.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-3 align-top" style={{ width: columnWidths.select }}>
                  <select
                    className="border rounded px-2 py-1 text-sm w-full bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
                    value={milestoneId || ""}
                    onChange={(e) =>
                      onAssign(event.id, {
                        project_id: projectId,
                        milestone_id: e.target.value ? Number(e.target.value) : undefined,
                      })
                    }
                    disabled={!projectId}
                  >
                    <option value="">–</option>
                    {milestoneOptions(projectId).map((milestone) => (
                      <option key={milestone.id} value={milestone.id}>
                        {milestone.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-3 align-top" style={{ width: columnWidths.select }}>
                  <select
                    className="border rounded px-2 py-1 text-sm w-full bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
                    value={assignment?.activity_type || getDefaultActivity(event) || ""}
                    onChange={(e) =>
                      onAssign(event.id, {
                        project_id: projectId,
                        milestone_id: milestoneId,
                        activity_type: e.target.value || undefined,
                        comment: assignment?.comment,
                      })
                    }
                    disabled={!projectId}
                  >
                    <option value="">–</option>
                    {activityOptions.map((activity) => (
                      <option key={activity} value={activity}>
                        {activity}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-3 align-top" style={{ width: columnWidths.select }}>
                  <select
                    className="border rounded px-2 py-1 text-sm w-full bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
                    value={event.is_private ? "private" : "standard"}
                    onChange={(e) => onPrivacyChange(event.id, e.target.value === "private")}
                  >
                    <option value="standard">Standard</option>
                    <option value="private">Privat</option>
                  </select>
                </td>
                <td className="px-2 py-3 align-top">
                  <input
                    className="border rounded px-2 py-1 text-sm w-full bg-white dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100"
                    value={assignment?.comment ?? getDefaultComment(event) ?? ""}
                    onChange={(e) =>
                      onAssign(event.id, {
                        project_id: projectId,
                        milestone_id: milestoneId,
                        activity_type: assignment?.activity_type,
                        comment: e.target.value,
                      })
                    }
                    disabled={!projectId}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
