import axios from "axios";
import dayjs from "dayjs";
import {
  Assignment,
  AssignmentPayload,
  Event,
  Filters,
  LoggingSettings,
  Milestone,
  Project,
  SourceType,
} from "./types";

export interface BluetoothCommandResult {
  stdout?: string;
  stderr?: string;
  returncode?: number;
}

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

export async function fetchAssignments(filters?: Filters): Promise<Assignment[]> {
  const params = new URLSearchParams();
  if (filters?.start) params.set("start", filters.start);
  if (filters?.end) params.set("end", filters.end);
  params.set("limit", "500");
  const { data } = await client.get<Assignment[]>("/assignments", { params });
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

export async function listBluetoothDevices() {
  const { data } = await client.get("/bluetooth/devices");
  return data.devices as { mac: string; name: string }[];
}

export async function scanBluetooth(timeout = 8) {
  const { data } = await client.post("/bluetooth/scan", undefined, { params: { timeout } });
  return data as {
    devices: { mac: string; name: string }[];
    scan_stdout?: string;
    scan_stderr?: string;
    devices_stdout?: string;
  };
}

export async function pairBluetooth(mac: string): Promise<BluetoothCommandResult> {
  const { data } = await client.post("/bluetooth/pair", { mac });
  return data as BluetoothCommandResult;
}

export async function connectBluetooth(mac: string): Promise<BluetoothCommandResult> {
  const { data } = await client.post("/bluetooth/connect", { mac });
  return data as BluetoothCommandResult;
}

export async function disconnectBluetooth(mac: string): Promise<BluetoothCommandResult> {
  const { data } = await client.post("/bluetooth/disconnect", { mac });
  return data as BluetoothCommandResult;
}

export async function removeBluetooth(mac: string): Promise<BluetoothCommandResult> {
  const { data } = await client.post("/bluetooth/remove", { mac });
  return data as BluetoothCommandResult;
}

export async function triggerPbap(mac: string) {
  const { data } = await client.post("/bluetooth/pbap", { mac });
  return data;
}

export async function allowIncomingPair(mac: string, duration = 60) {
  const { data } = await client.post("/bluetooth/incoming", { mac, duration });
  return data as { expires_at: number; mac: string; duration: number };
}

export async function fetchIncomingPairingStatus() {
  const { data } = await client.get("/bluetooth/incoming/status");
  return data as { active: boolean; mac?: string; expires_at?: number };
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

export interface BulkUpdateOptions {
  is_private?: boolean;
  delete?: boolean;
  unassign?: boolean;
}

export interface BulkUpdateResponse {
  updated_count: number;
  deleted_count: number;
  unassigned_count: number;
  event_ids: number[];
}

export async function bulkUpdateEvents(
  eventIds: number[],
  options: BulkUpdateOptions
): Promise<BulkUpdateResponse> {
  const payload = {
    event_ids: eventIds,
    is_private: options.is_private,
    delete: options.delete || false,
    unassign: options.unassign || false,
  };
  const { data } = await client.patch<BulkUpdateResponse>("/events/bulk", payload);
  return data;
}

export async function fetchUnassignedEvents(userId?: string, limit = 20): Promise<Event[]> {
  const params = new URLSearchParams();
  if (userId) params.set("user_id", userId);
  params.set("limit", limit.toString());
  const { data } = await client.get<Event[]>("/events/unassigned", { params });
  return data;
}

export async function createBulkAssignments(
  eventIds: number[],
  payload: Omit<AssignmentPayload, "event_id">
) {
  const { data } = await client.post("/assignments/bulk", {
    event_ids: eventIds,
    ...payload,
  });
  return data;
}

export async function uploadProjectCsv(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  try {
    const { data } = await client.post("/import/projects", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  } catch (error: any) {
    console.error("CSV upload error:", error);
    console.error("Response data:", error.response?.data);
    console.error("Response status:", error.response?.status);
    throw error;
  }
}
