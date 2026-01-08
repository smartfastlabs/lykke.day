export type UserStatus = "active" | "new-lead";

export interface UserSettings {
  template_defaults: string[];
}

export interface UserSettingsUpdate {
  template_defaults?: string[];
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

