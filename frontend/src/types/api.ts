/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export type ActionType =
  | "COMPLETE"
  | "DELETE"
  | "EDIT"
  | "NOTIFY"
  | "PAUSE"
  | "PUNT"
  | "RESUME"
  | "START"
  | "VIEW";
export type AlarmType = "GENTLE" | "FIRM" | "LOUD" | "SIREN";
export type DayTag = "WEEKEND" | "VACATION" | "WORKDAY";
export type DayStatus =
  | "UNSCHEDULED"
  | "SCHEDULED"
  | "IN_PROGRESS"
  | "COMPLETE";
export type TaskFrequency =
  | "DAILY"
  | "CUSTOM_WEEKLY"
  | "WEEKLY"
  | "ONCE"
  | "YEARLY"
  | "MONTHLY"
  | "BI_WEEKLY"
  | "WORK_DAYS"
  | "WEEKENDS";
export type TaskStatus =
  | "COMPLETE"
  | "NOT_READY"
  | "READY"
  | "PUNT"
  | "NOT_STARTED"
  | "PENDING";
export type TaskType = "MEAL" | "EVENT" | "CHORE" | "ERRAND" | "ACTIVITY";
export type TaskCategory = "HYGIENE" | "NUTRITION" | "HEALTH" | "PET" | "HOUSE";
export type TimingType = "DEADLINE" | "FIXED_TIME" | "TIME_WINDOW" | "FLEXIBLE";
export type TaskTag =
  | "AVOIDANT"
  | "FORGETTABLE"
  | "IMPORTANT"
  | "URGENT"
  | "FUN";
export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export interface Action {
  id?: string;
  type: ActionType;
  data?: {
    [k: string]: unknown;
  };
  created_at?: string;
}
export interface Alarm {
  id?: string;
  name: string;
  time: string;
  type: AlarmType;
  description?: string | null;
  triggered_at?: string | null;
}
export interface AuthToken {
  id?: string;
  user_id: string;
  platform: string;
  token: string;
  refresh_token?: string | null;
  token_uri?: string | null;
  client_id?: string | null;
  client_secret?: string | null;
  scopes?: unknown[] | null;
  expires_at?: string | null;
  created_at?: string;
}
export interface BaseConfigObject {
  id?: string;
}
/**
 * Base class for entities that have a date associated with them.
 *
 * Entities can either implement _get_date() to return a date directly,
 * or implement _get_datetime() and provide a timezone to convert to date.
 */
export interface BaseDateObject {
  id?: string;
  /**
   * Get the date for this entity.
   *
   * If _get_date() is implemented, it takes precedence.
   * Otherwise, uses _get_datetime() with the configured timezone.
   */
  date: string;
}
export interface BaseEntityObject {
  id?: string;
}
export interface BaseObject {}
export interface Calendar {
  id?: string;
  user_id: string;
  name: string;
  auth_token_id: string;
  platform_id: string;
  platform: string;
  last_sync_at?: string | null;
}
export interface Day {
  id?: string;
  user_id: string;
  date: string;
  template_id: string;
  tags?: DayTag[];
  alarm?: Alarm | null;
  status?: DayStatus;
  scheduled_at?: string | null;
}
export interface DayContext {
  day: Day;
  events?: Event[];
  tasks?: Task[];
  messages?: Message[];
}
export interface Event {
  id?: string;
  user_id: string;
  name: string;
  calendar_id: string;
  platform_id: string;
  platform: string;
  status: string;
  starts_at: string;
  frequency: TaskFrequency;
  ends_at?: string | null;
  created_at?: string;
  updated_at?: string;
  people?: Person[];
  actions?: Action[];
  /**
   * Get the date for this event.
   */
  date: string;
}
export interface Person {
  id?: string;
  name?: string | null;
  email?: string | null;
  phone_number?: string | null;
  relationship?: string | null;
}
export interface Task {
  id?: string;
  user_id: string;
  scheduled_date: string;
  name: string;
  status: TaskStatus;
  task_definition: TaskDefinition;
  category: TaskCategory;
  frequency: TaskFrequency;
  completed_at?: string | null;
  schedule?: TaskSchedule | null;
  routine_id?: string | null;
  tags?: TaskTag[];
  actions?: Action[];
  /**
   * Get the date for this entity.
   *
   * If _get_date() is implemented, it takes precedence.
   * Otherwise, uses _get_datetime() with the configured timezone.
   */
  date: string;
}
export interface TaskDefinition {
  id?: string;
  user_id: string;
  name: string;
  description: string;
  type: TaskType;
}
export interface TaskSchedule {
  available_time?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  timing_type: TimingType;
}
export interface Message {
  id?: string;
  user_id: string;
  author: "system" | "agent" | "user";
  sent_at: string;
  content: string;
  read_at?: string | null;
  /**
   * Get the date for this entity.
   *
   * If _get_date() is implemented, it takes precedence.
   * Otherwise, uses _get_datetime() with the configured timezone.
   */
  date: string;
}
export interface DayTemplate {
  id?: string;
  user_id: string;
  slug: string;
  tasks?: string[];
  alarm?: Alarm | null;
  icon?: string | null;
}
export interface NotificationAction {
  id?: string;
  action: string;
  title: string;
  icon?: string | null;
}
export interface NotificationPayload {
  id?: string;
  title: string;
  body: string;
  icon?: string | null;
  badge?: string | null;
  tag?: string | null;
  actions?: NotificationAction[];
  data?: {
    [k: string]: unknown;
  } | null;
}
export interface PushSubscription {
  id?: string;
  user_id: string;
  device_name?: string | null;
  endpoint: string;
  p256dh: string;
  auth: string;
  createdAt?: string;
}
export interface Routine {
  id?: string;
  user_id: string;
  name: string;
  category: TaskCategory;
  routine_schedule: RoutineSchedule;
  description?: string;
  tasks?: RoutineTask[];
}
export interface RoutineSchedule {
  frequency: TaskFrequency;
  weekdays?: DayOfWeek[] | null;
}
export interface RoutineTask {
  task_definition_id: string;
  name?: string | null;
  schedule?: TaskSchedule | null;
}
export interface User {
  id?: string;
  email: string;
  phone_number?: string | null;
  hashed_password: string;
  settings?: UserSetting;
  created_at?: string;
  updated_at?: string | null;
}
export interface UserSetting {
  template_defaults?: string[];
}
