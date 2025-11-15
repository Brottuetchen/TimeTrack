import { useEffect, useMemo, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import dayjs from "dayjs";
import { FiltersBar } from "./components/FiltersBar";
import { EventsTable } from "./components/EventsTable";
import { BulkAssignBar } from "./components/BulkAssignBar";
import { MasterdataImport } from "./components/MasterdataImport";
import { BluetoothSetup } from "./components/BluetoothSetup";
import { PrivacyControls } from "./components/PrivacyControls";
import {
  createAssignment,
  defaultRange,
  exportCsv,
  fetchAssignments,
  fetchEvents,
  fetchMilestones,
  fetchProjects,
  updateEventPrivacy,
  updateAssignment,
  uploadProjectCsv,
} from "./api";
import { Assignment, BulkForm, Event, Filters, Milestone, Project } from "./types";

const ACTIVITY_OPTIONS = ["Planung", "Baustelle", "Dokumentation", "Meeting", "Fahrt", "Telefon", "PC"];

function App() {
  const [filters, setFilters] = useState<Filters>(defaultRange());
  const [events, setEvents] = useState<Event[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [bulkForm, setBulkForm] = useState<BulkForm>({});
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window === "undefined") return "light";
    return (localStorage.getItem("tt-theme") as "light" | "dark") || "light";
  });

  const assignmentMap = useMemo(() => {
    const map: Record<number, Assignment> = {};
    assignments.forEach((assignment) => {
      map[assignment.event.id] = assignment;
    });
    return map;
  }, [assignments]);

  const eventMap = useMemo(() => {
    const map: Record<number, Event> = {};
    events.forEach((event) => {
      map[event.id] = event;
    });
    return map;
  }, [events]);

  const defaultActivity = (event?: Event) => {
    if (!event) return "";
    return event.source_type === "phone" ? "Telefon" : "PC";
  };

  const defaultComment = (event?: Event) => {
    if (!event) return "";
    if (event.source_type === "phone") {
      const contact = event.contact_name || "Unbekannt";
      const number = event.phone_number ? ` (${event.phone_number})` : "";
      return `Anruf von ${contact}${number}`;
    }
    const title = event.window_title || event.process_name;
    return title || "Fensteraktivität";
  };

  useEffect(() => {
    loadStatic();
  }, []);

  const loadStatic = async () => {
    try {
      const [proj, miles] = await Promise.all([fetchProjects(), fetchMilestones()]);
      setProjects(proj);
      setMilestones(miles);
    } catch (err) {
      console.error(err);
      toast.error("Konnte Stammdaten nicht laden");
    }
  };

  const loadEvents = async () => {
    setLoading(true);
    try {
      const [evts, assigns] = await Promise.all([fetchEvents(filters), fetchAssignments()]);
      setEvents(evts);
      setAssignments(assigns);
      setSelected(new Set());
      toast.success(`Events aktualisiert (${evts.length})`);
    } catch (err) {
      console.error(err);
      toast.error("Fehler beim Laden");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("tt-theme", theme);
  }, [theme]);

  const handleAssign = async (eventId: number, payload: BulkForm) => {
    if (!payload.project_id) {
      toast.error("Projekt erforderlich");
      return;
    }
    const current = assignmentMap[eventId];
    const eventObj = eventMap[eventId];
    const mergedPayload: BulkForm = { ...payload };
    if (!mergedPayload.activity_type && eventObj) {
      mergedPayload.activity_type = defaultActivity(eventObj);
    }
    if (mergedPayload.comment === undefined && eventObj && !current) {
      mergedPayload.comment = defaultComment(eventObj);
    }
    try {
      if (current) {
        setAssignments((prev) =>
          prev.map((assignment) => {
            if (assignment.id !== current.id) return assignment;
            return {
              ...assignment,
              project: projects.find((p) => p.id === mergedPayload.project_id) || assignment.project,
              milestone: milestones.find((m) => m.id === mergedPayload.milestone_id) || undefined,
              activity_type: mergedPayload.activity_type,
              comment: mergedPayload.comment,
            };
          }),
        );
        await updateAssignment(current.id, {
          project_id: mergedPayload.project_id,
          milestone_id: mergedPayload.milestone_id,
          activity_type: mergedPayload.activity_type,
          comment: mergedPayload.comment,
        });
      } else {
        const response = await createAssignment({
          event_id: eventId,
          project_id: mergedPayload.project_id!,
          milestone_id: mergedPayload.milestone_id,
          activity_type: mergedPayload.activity_type,
          comment: mergedPayload.comment,
        });
        setAssignments((prev) => [...prev, response]);
      }
    } catch (err) {
      console.error(err);
      toast.error("Zuweisung fehlgeschlagen");
    }
  };

  const toggleSelect = (eventId: number, checked: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(eventId);
      } else {
        next.delete(eventId);
      }
      return next;
    });
  };

  const applyBulk = async () => {
    if (!bulkForm.project_id) {
      toast.error("Projekt wählen");
      return;
    }
    const ids = Array.from(selected);
    if (!ids.length) return;
    try {
      for (const id of ids) {
        // eslint-disable-next-line no-await-in-loop
        await handleAssign(id, bulkForm);
      }
      toast.success("Bulk-Zuweisung erledigt");
      setSelected(new Set());
    } catch (err) {
      console.error(err);
      toast.error("Bulk fehlgeschlagen");
    }
  };

  const handleMasterdataUpload = async (file: File) => {
    try {
      const result = await uploadProjectCsv(file);
      toast.success(
        `Import ok: ${result.projects_created} neu / ${result.projects_updated} aktualisiert, Milestones ${result.milestones_created} neu / ${result.milestones_updated} aktualisiert`,
      );
      await loadStatic();
      await loadEvents();
    } catch (err) {
      console.error(err);
      toast.error("Import fehlgeschlagen");
    }
  };

  const handlePrivacyChange = async (eventId: number, isPrivate: boolean) => {
    try {
      await updateEventPrivacy(eventId, isPrivate);
      setEvents((prev) => prev.map((event) => (event.id === eventId ? { ...event, is_private: isPrivate } : event)));
      toast.success(isPrivate ? "Event als privat markiert" : "Event wieder sichtbar");
    } catch (err) {
      console.error(err);
      toast.error("Privacy-Markierung fehlgeschlagen");
    }
  };

  const toggleTheme = () => setTheme((prev) => (prev === "light" ? "dark" : "light"));

  return (
    <div className="min-h-screen px-6 py-6 space-y-6 bg-slate-100 text-slate-900 dark:bg-slate-900 dark:text-slate-100 transition-colors">
      <Toaster position="bottom-right" />
      <header className="flex flex-wrap items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">TimeTrack Review</h1>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            {dayjs(filters.start).format("DD.MM")} – {dayjs(filters.end).format("DD.MM.YYYY")}
          </p>
        </div>
        <div className="ml-auto flex gap-2 items-center">
          <button
            onClick={toggleTheme}
            className="px-3 py-2 rounded border border-slate-300 dark:border-slate-600 hover:bg-slate-200 dark:hover:bg-slate-700"
            title="Dark Mode umschalten"
          >
            {theme === "dark" ? "🌙" : "☀️"}
          </button>
          <button
            onClick={() => exportCsv(filters)}
            className="px-4 py-2 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700"
          >
            CSV Export
          </button>
          <button
            onClick={loadEvents}
            className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-500 dark:bg-blue-500 dark:hover:bg-blue-400"
          >
            Neu laden
          </button>
        </div>
      </header>
      <FiltersBar filters={filters} onChange={setFilters} onRefresh={loadEvents} />
      <MasterdataImport onUpload={handleMasterdataUpload} />
      {selected.size > 0 && (
        <BulkAssignBar
          selectedCount={selected.size}
          bulkForm={bulkForm}
          projects={projects}
          milestones={milestones}
          activityOptions={ACTIVITY_OPTIONS}
          onChange={setBulkForm}
          onApply={applyBulk}
          onClear={() => setSelected(new Set())}
        />
      )}
      <section>
        {loading ? (
          <div className="p-6 text-center text-slate-500">Lädt…</div>
        ) : (
          <EventsTable
            events={events}
            assignments={assignmentMap}
            projects={projects}
            milestones={milestones}
            selectedIds={selected}
            onSelect={toggleSelect}
            onAssign={handleAssign}
            activityOptions={ACTIVITY_OPTIONS}
            getDefaultActivity={defaultActivity}
            getDefaultComment={defaultComment}
            onPrivacyChange={handlePrivacyChange}
          />
        )}
      </section>
      <PrivacyControls />
      <BluetoothSetup />
    </div>
  );
}

export default App;
