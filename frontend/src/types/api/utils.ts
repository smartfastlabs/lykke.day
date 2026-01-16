/**
 * Type utilities for API responses.
 * These types work with the OpenAPI-generated types.
 */

import type { components } from './api.generated';

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
export type Day = components["schemas"]["DaySchema"];

// DayContext with events alias
type BaseDayContext = components["schemas"]["DayContextSchema"];
export type DayContext = Omit<BaseDayContext, 'calendar_entries'> & {
  events?: Event[];
  calendar_entries?: Event[];
  tasks?: Task[];
  goals?: Goal[];
};

export type DayTemplate = components["schemas"]["DayTemplateSchema"];
export type TimeBlockDefinition = components["schemas"]["TimeBlockDefinitionSchema"];
export type Calendar = components["schemas"]["CalendarSchema"];
export type CalendarEntrySeries = components["schemas"]["CalendarEntrySeriesSchema"];
export type TaskDefinition = components["schemas"]["TaskDefinitionSchema"];
export type Routine = components["schemas"]["RoutineSchema"];
export type RoutineTask = components["schemas"]["RoutineTaskSchema-Output"];
export type PushSubscription = components["schemas"]["PushSubscriptionSchema"];

// Value object types
export type TaskSchedule = components["schemas"]["TaskScheduleSchema"];
export type RoutineSchedule = components["schemas"]["RoutineScheduleSchema"];
export type Action = components["schemas"]["ActionSchema"];
export type Alarm = components["schemas"]["AlarmSchema"];

// Goal types - manually defined as they may not be in generated types yet
export interface Goal {
  id: string;
  name: string;
  status: GoalStatus;
  created_at?: string | null;
}

// Enum types
export type TaskStatus = components["schemas"]["TaskStatus"];
export type TaskType = components["schemas"]["TaskType"];
export type TaskFrequency = components["schemas"]["TaskFrequency"];
export type TaskCategory = components["schemas"]["TaskCategory"];
export type DayOfWeek = components["schemas"]["DayOfWeek"];
export type TimingType = components["schemas"]["TimingType"];
export type TimeBlockType = components["schemas"]["TimeBlockType"];
export type TimeBlockCategory = components["schemas"]["TimeBlockCategory"];
export type ActionType = components["schemas"]["ActionType"];

// GoalStatus enum - manually defined as it may not be in generated types yet
export type GoalStatus = "INCOMPLETE" | "COMPLETE" | "PUNT";

