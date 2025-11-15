import axios from "axios";
import dayjs from "dayjs";
import { Assignment, AssignmentPayload, Event, Filters, LoggingSettings, Milestone, Project, SourceType } from "./types";

const runtimeBase =
  typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:${import.meta.env.VITE_API_PORT || "8000"}`
    : "http://localhost:8000";
const API_BASE = import.meta.env.VITE_API_BASE || runtimeBase;

const client = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

export async function fetchEvents(filters: Filters): Promise<Event[]> {
  const params = new URLSearchParams();
  if (filters.start) params.set("start", filters.start);
  if (filters.end) params.set("end", filters.end);
  if (filters.source && filters.source !== "all") params.set("source_type", filters.source);
  if (filters.user) params.set("user_id", filters.user);
  params.set("limit", "500");
  const { data } = await client.get<Event[]>("/events", { params });
  return data;
}

export async function fetchProjects(): Promise<Project[]> {
  const { data } = await client.get<Project[]>("/projects");
  return data;
}

export async function fetchMilestones(project_id?: number): Promise<Milestone[]> {
  const params = project_id ? { project_id } : undefined;
  const { data } = await client.get<Milestone[]>("/milestones", { params });
  return data;
}

export async function fetchAssignments(): Promise<Assignment[]> {
  const { data } = await client.get<Assignment[]>("/assignments");
  return data;
}

export async function fetchLoggingSettings(): Promise<LoggingSettings> {
  const { data } = await client.get<LoggingSettings>("/settings/logging");
  return data;
}

export async function saveLoggingSettings(payload: Partial<LoggingSettings>) {
  const { data } = await client.put("/settings/logging", payload);
  return data as LoggingSettings;
}

export async function activatePrivacyMode(durationMinutes?: number) {
  const { data } = await client.post("/settings/privacy", {
    duration_minutes: durationMinutes,
    indefinite: !durationMinutes,
  });
  return data as LoggingSettings;
}

export async function clearPrivacyMode() {
  const { data } = await client.post("/settings/privacy/clear");
  return data as LoggingSettings;
}

export async function createAssignment(payload: AssignmentPayload) {
  const { data } = await client.post("/assignments", payload);
  return data;
}

export async function updateAssignment(id: number, payload: Partial<AssignmentPayload>) {
  const { data } = await client.put(`/assignments/${id}`, payload);
  return data;
}

export function exportCsv(filters: Filters) {
  const params = new URLSearchParams();
  if (filters.start) params.set("start", filters.start);
  if (filters.end) params.set("end", filters.end);
  if (filters.source && filters.source !== "all") params.set("source_type", filters.source);
  const url = `${API_BASE}/export/csv?${params.toString()}`;
  window.open(url, "_blank");
}

export function defaultRange(): Filters {
  const today = dayjs().startOf("day");
  return {
    start: today.subtract(7, "day").toISOString(),
    end: today.add(1, "day").toISOString(),
    source: "all",
    user: "",
  };
}

export async function updateEventPrivacy(eventId: number, isPrivate: boolean) {
  const { data } = await client.patch(`/events/${eventId}`, { is_private: isPrivate });
  return data as Event;
}

export async function uploadProjectCsv(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post("/import/projects", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
