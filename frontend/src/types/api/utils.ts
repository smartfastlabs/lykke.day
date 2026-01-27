/**
 * Type utilities for API responses.
 * These types work with the OpenAPI-generated types.
 */

import type { components } from "./api.generated";
import type { LLMRunResultSnapshot } from "./notification";

// API Response wrapper type
export interface ApiResponse<T> {
  data: T;
  status: number;
  ok: boolean;
}

// Paginated response type
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}

// Error response type
export interface ApiError {
  detail: string;
  status_code?: number;
}

// Re-export commonly used schema types for convenience
// Entity types
export type Task = components["schemas"]["TaskSchema"];
export type Event = components["schemas"]["CalendarEntrySchema"];
export type Day = components["schemas"]["DaySchema"] & {
  reminders?: Reminder[];
  alarms?: Alarm[];
  brain_dump_items?: BrainDumpItem[];
};

// DayContext with events alias
type BaseDayContext = components["schemas"]["DayContextSchema"];
export type DayContext = Omit<BaseDayContext, "calendar_entries"> & {
  events?: Event[];
  calendar_entries?: Event[];
  tasks?: Task[];
  reminders?: Reminder[];
  alarms?: Alarm[];
};

export type DayTemplate = components["schemas"]["DayTemplateSchema"] & {
  alarms?: Alarm[];
};
export type TimeBlockDefinition =
  components["schemas"]["TimeBlockDefinitionSchema"];
export type Calendar = components["schemas"]["CalendarSchema"];
export type CalendarEntrySeries =
  components["schemas"]["CalendarEntrySeriesSchema"];
export type TaskDefinition = components["schemas"]["TaskDefinitionSchema"];
export type TaskDefinitionCreate =
  components["schemas"]["TaskDefinitionCreateSchema"];
export type RoutineDefinition =
  components["schemas"]["RoutineDefinitionSchema"] & {
    time_window?: TimeWindow | null;
  };
export type TimeWindow = {
  available_time?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  cutoff_time?: string | null;
};
export type RoutineDefinitionTask =
  components["schemas"]["RoutineDefinitionTaskSchema-Output"] & {
    time_window?: TimeWindow | null;
  };
export type PushSubscription = components["schemas"]["PushSubscriptionSchema"];

// Value object types
export type RecurrenceSchedule =
  components["schemas"]["RecurrenceScheduleSchema"];
export type Action = components["schemas"]["ActionSchema"];

// Reminder types - manually defined as they may not be in generated types yet
export interface Reminder {
  id: string;
  name: string;
  status: ReminderStatus;
  created_at?: string | null;
}

export interface Alarm {
  id?: string | null;
  name: string;
  time: string;
  datetime?: string | null;
  type: AlarmType;
  url: string;
  status?: AlarmStatus;
  snoozed_until?: string | null;
}

export interface AlarmPreset {
  id?: string | null;
  name?: string | null;
  time?: string | null;
  type?: AlarmType;
  url?: string | null;
}

export type BrainDumpItem = components["schemas"]["BrainDumpItemSchema"] & {
  llm_run_result?: LLMRunResultSnapshot | Record<string, unknown> | null;
};

// Enum types
export type TaskStatus = components["schemas"]["TaskStatus"];
export type TaskType = components["schemas"]["TaskType"];
export type TaskFrequency = components["schemas"]["TaskFrequency"];
export type TaskCategory = components["schemas"]["TaskCategory"];
export type DayOfWeek = components["schemas"]["DayOfWeek"];
export type TimeBlockType = components["schemas"]["TimeBlockType"];
export type TimeBlockCategory = components["schemas"]["TimeBlockCategory"];
export type ActionType = components["schemas"]["ActionType"];

// ReminderStatus enum - manually defined as it may not be in generated types yet
export type ReminderStatus = "INCOMPLETE" | "COMPLETE" | "PUNT";

export type AlarmType = "URL" | "GENERIC";
export type AlarmStatus = "ACTIVE" | "TRIGGERED" | "SNOOZED" | "CANCELLED";

export type BrainDumpItemStatus = "ACTIVE" | "COMPLETE" | "PUNT";
export type BrainDumpItemType = components["schemas"]["BrainDumpItemType"];

// UseCase Config types
export interface UseCaseConfig {
  id: string;
  user_id: string;
  usecase: string;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
}

export interface NotificationUseCaseConfig {
  user_amendments: string[];
  rendered_prompt?: string;
}
