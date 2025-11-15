export type SourceType = "phone" | "window";
export type CallDirection = "INCOMING" | "OUTGOING" | "MISSED";

export interface Event {
  id: number;
  source_type: SourceType;
  timestamp_start: string;
  timestamp_end?: string;
  duration_seconds?: number;
  is_private: boolean;
  phone_number?: string;
  contact_name?: string;
  direction?: CallDirection;
  window_title?: string;
  process_name?: string;
  machine_id?: string;
  device_id?: string;
  user_id?: string;
}

export interface Project {
  id: number;
  name: string;
  kunde?: string;
  notizen?: string;
}

export interface Milestone {
  id: number;
  project_id: number;
  name: string;
  soll_stunden?: number;
  ist_stunden?: number;
  bonus_relevant: boolean;
}

export interface Assignment {
  id: number;
  event: Event;
  project: Project;
  milestone?: Milestone;
  activity_type?: string;
  comment?: string;
}

export interface AssignmentPayload {
  event_id: number;
  project_id: number;
  milestone_id?: number;
  activity_type?: string;
  comment?: string;
}

export interface Filters {
  start: string;
  end: string;
  source?: SourceType | "all";
  user?: string;
}

export interface BulkForm {
  project_id?: number;
  milestone_id?: number;
  activity_type?: string;
  comment?: string;
}

export interface LoggingSettings {
  whitelist: string[];
  blacklist: string[];
  bluetooth_enabled: boolean;
  privacy_mode_until: string | null;
  server_time: string;
}
