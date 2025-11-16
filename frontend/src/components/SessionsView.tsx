import { useState, useEffect } from "react";
import dayjs from "dayjs";
import clsx from "clsx";
import { Session, Project, Milestone } from "../types";
import { fetchSessions, fetchProjects, fetchMilestones, assignSession, triggerAggregation } from "../api";

interface Props {
  userId: string;
  startDate: string;
  endDate: string;
}

export function SessionsView({ userId, startDate, endDate }: Props) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loading, setLoading] = useState(false);
  const [aggregating, setAggregating] = useState(false);

  useEffect(() => {
    loadData();
  }, [userId, startDate, endDate]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sessionsData, projectsData, milestonesData] = await Promise.all([
        fetchSessions({ user_id: userId, start: startDate, end: endDate, limit: 100 }),
        fetchProjects(),
        fetchMilestones(),
      ]);
      setSessions(sessionsData);
      setProjects(projectsData);
      setMilestones(milestonesData);
    } catch (error) {
      console.error("Error loading sessions:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerAggregation = async () => {
    setAggregating(true);
    try {
      const result = await triggerAggregation({
        user_id: userId,
        start: startDate,
        end: endDate,
      });
      alert(`✓ ${result.sessions_created} Sessions erstellt (100% lokal)`);
      loadData();
    } catch (error) {
      console.error("Error triggering aggregation:", error);
      alert("Fehler beim Aggregieren");
    } finally {
      setAggregating(false);
    }
  };

  const handleAssignSession = async (sessionId: number, projectId: number) => {
    if (!projectId) return;

    try {
      await assignSession(sessionId, {
        project_id: projectId,
        comment: "Assigned from session view",
      });
      loadData();
    } catch (error) {
      console.error("Error assigning session:", error);
      alert("Fehler beim Zuweisen");
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const formatTime = (dateStr: string) => {
    return dayjs(dateStr).format("HH:mm");
  };

  const totalActiveDuration = sessions.reduce((sum, s) => sum + s.active_duration_seconds, 0);
  const totalEvents = sessions.reduce((sum, s) => sum + s.event_count, 0);

  if (loading) {
    return <div className="p-4">Lade Sessions...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Header mit Aggregation-Button */}
      <div className="flex items-center justify-between bg-white dark:bg-slate-800 p-4 rounded-md border border-slate-200 dark:border-slate-700">
        <div>
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
            📊 Sessions ({sessions.length})
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {totalEvents} Events aggregiert • {formatDuration(totalActiveDuration)} aktive Zeit
          </p>
        </div>
        <button
          onClick={handleTriggerAggregation}
          disabled={aggregating}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-md disabled:opacity-50"
        >
          {aggregating ? "Aggregiere..." : "🔄 Neu aggregieren"}
        </button>
      </div>

      {/* Info-Box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3 text-sm">
        <strong>ℹ️ 100% Lokal:</strong> Alle Aggregationen laufen auf dem Pi. Keine Cloud, keine externen APIs.
      </div>

      {/* Sessions-Tabelle */}
      <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 dark:bg-slate-700 text-left text-xs font-semibold uppercase text-slate-500 dark:text-slate-200">
            <tr>
              <th className="px-2 py-3">Zeit</th>
              <th className="px-2 py-3">Prozess</th>
              <th className="px-2 py-3">Fenster-Titel</th>
              <th className="px-2 py-3">Dauer</th>
              <th className="px-2 py-3">Events</th>
              <th className="px-2 py-3">Projekt</th>
            </tr>
          </thead>
          <tbody>
            {sessions.length === 0 && (
              <tr>
                <td colSpan={6} className="px-2 py-8 text-center text-slate-500 dark:text-slate-400">
                  Keine Sessions vorhanden. Klicke auf "Neu aggregieren" um Events zu Sessions zu kombinieren.
                </td>
              </tr>
            )}
            {sessions.map((session) => (
              <tr
                key={session.id}
                className={clsx(
                  "border-b border-slate-200 dark:border-slate-700 last:border-b-0 hover:bg-slate-50 dark:hover:bg-slate-700",
                  session.is_private && "opacity-60"
                )}
              >
                <td className="px-2 py-3 align-top text-slate-800 dark:text-slate-100">
                  <div className="font-mono text-xs">
                    {formatTime(session.start_time)} - {formatTime(session.end_time)}
                  </div>
                </td>
                <td className="px-2 py-3 align-top text-slate-800 dark:text-slate-100">
                  <div className="font-medium truncate max-w-[150px]" title={session.process_name}>
                    {session.process_name}
                  </div>
                </td>
                <td className="px-2 py-3 align-top text-slate-800 dark:text-slate-100">
                  <div className="truncate max-w-[300px]" title={session.window_title_base || ""}>
                    {session.window_title_base || <span className="text-slate-400">-</span>}
                  </div>
                </td>
                <td className="px-2 py-3 align-top text-slate-800 dark:text-slate-100">
                  <div className="font-semibold">{formatDuration(session.active_duration_seconds)}</div>
                  {session.break_count > 0 && (
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      {session.break_count} Pausen
                    </div>
                  )}
                </td>
                <td className="px-2 py-3 align-top text-slate-800 dark:text-slate-100">
                  <div className="text-center">
                    <span className="inline-block px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-xs">
                      {session.event_count}
                    </span>
                  </div>
                </td>
                <td className="px-2 py-3 align-top">
                  <select
                    value={session.assignment_id ? projects.find(p => p.id === session.assignment?.project?.id)?.id || "" : ""}
                    onChange={(e) => {
                      const projectId = parseInt(e.target.value);
                      if (projectId) handleAssignSession(session.id, projectId);
                    }}
                    className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-2 py-1 text-sm text-slate-800 dark:text-slate-100"
                  >
                    <option value="">-- Projekt wählen --</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Statistiken */}
      {sessions.length > 0 && (
        <div className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md p-4">
          <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-2">Statistiken</h3>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-slate-500 dark:text-slate-400">Sessions</div>
              <div className="font-semibold text-lg text-slate-800 dark:text-slate-100">{sessions.length}</div>
            </div>
            <div>
              <div className="text-slate-500 dark:text-slate-400">Events</div>
              <div className="font-semibold text-lg text-slate-800 dark:text-slate-100">{totalEvents}</div>
            </div>
            <div>
              <div className="text-slate-500 dark:text-slate-400">Aktive Zeit</div>
              <div className="font-semibold text-lg text-slate-800 dark:text-slate-100">
                {formatDuration(totalActiveDuration)}
              </div>
            </div>
            <div>
              <div className="text-slate-500 dark:text-slate-400">Ø Events/Session</div>
              <div className="font-semibold text-lg text-slate-800 dark:text-slate-100">
                {Math.round(totalEvents / sessions.length)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
