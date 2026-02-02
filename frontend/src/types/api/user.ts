import type { AlarmPreset } from "./utils";

export type UserStatus = "active" | "new-lead";
export type LLMProvider = "anthropic" | "openai";
export type CalendarEntryNotificationChannel = "PUSH" | "TEXT" | "KIOSK_ALARM";

export interface CalendarEntryNotificationRule {
  channel: CalendarEntryNotificationChannel;
  minutes_before: number;
}

export interface CalendarEntryNotificationSettings {
  enabled: boolean;
  rules: CalendarEntryNotificationRule[];
}

export interface UserSettings {
  template_defaults: string[];
  llm_provider?: LLMProvider | null;
  timezone?: string | null;
  base_personality_slug?: string;
  llm_personality_amendments: string[];
  morning_overview_time?: string | null; // HH:MM[:SS] format in user's local timezone
  alarm_presets?: AlarmPreset[];
  calendar_entry_notification_settings?: CalendarEntryNotificationSettings;
}

export interface UserSettingsUpdate {
  template_defaults?: string[];
  llm_provider?: LLMProvider | null;
  timezone?: string | null;
  base_personality_slug?: string | null;
  llm_personality_amendments?: string[] | null;
  morning_overview_time?: string | null; // HH:MM[:SS] format in user's local timezone
  alarm_presets?: AlarmPreset[] | null;
  calendar_entry_notification_settings?:
    | CalendarEntryNotificationSettings
    | null;
}

export interface CurrentUser {
  id: string;
  email: string;
  phone_number?: string | null;
  status: UserStatus;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  settings: UserSettings;
  created_at: string;
  updated_at: string | null;
}

export interface UserProfileUpdate {
  phone_number?: string | null;
  status?: UserStatus;
  is_active?: boolean;
  is_superuser?: boolean;
  is_verified?: boolean;
  settings?: UserSettingsUpdate;
}

export interface BasePersonalityOption {
  slug: string;
  label: string;
}
