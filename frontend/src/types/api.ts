/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type TimingType = "DEADLINE" | "FIXED_TIME" | "TIME_WINDOW" | "FLEXIBLE";
export type Frequency = "DAILY" | "CUSTOM_WEEKLY";
export type Category = "hygiene" | "nutrition" | "health" | "pet" | "chore";
export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6;
export type TaskStatus = "COMPLETE" | "NOT_READY" | "READY" | "PUNTED";

export interface AuthToken {
  platform: string;
  token: string;
  refresh_token?: string | null;
  token_uri?: string | null;
  client_id?: string | null;
  client_secret?: string | null;
  scopes?: unknown[] | null;
  expires_at?: string | null;
  uuid?: string;
  created_at?: string;
}
export interface BaseObject {}
export interface Calendar {
  name: string;
  auth_token_uuid: string;
  platform_id: string;
  platform: string;
  last_sync_at?: string | null;
}
export interface Day {
  date: string;
  events: Event[];
  tasks: Task[];
}
export interface Event {
  name: string;
  calendar_id: string;
  platform_id: string;
  platform: string;
  status: string;
  starts_at: string;
  ends_at?: string | null;
  created_at?: string;
  updated_at?: string;
  date: string;
  guid: string;
}
export interface Task {
  routine: Routine;
  date: string;
  status: TaskStatus;
  completed_at?: string | null;
}
export interface Routine {
  id?: string;
  name: string;
  description: string;
  timing_type: TimingType;
  frequency: Frequency;
  category: Category;
  available_time?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  schedule_days?: DayOfWeek[] | null;
}
export interface PushSubscription {
  endpoint: string;
  p256dh: string;
  auth: string;
  uuid?: string;
  createdAt?: string;
}
