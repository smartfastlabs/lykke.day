export type UserStatus = "active" | "new-lead";
export type LLMProvider = "anthropic" | "openai";

export interface UserSettings {
  template_defaults: string[];
  llm_provider?: LLMProvider | null;
  timezone?: string | null;
  base_personality_slug?: string;
  llm_personality_amendments: string[];
  morning_overview_time?: string | null; // HH:MM format in user's local timezone
}

export interface UserSettingsUpdate {
  template_defaults?: string[];
  llm_provider?: LLMProvider | null;
  timezone?: string | null;
  base_personality_slug?: string | null;
  llm_personality_amendments?: string[] | null;
  morning_overview_time?: string | null; // HH:MM format in user's local timezone
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

