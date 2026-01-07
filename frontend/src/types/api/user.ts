export interface UserSettings {
  template_defaults: string[];
}

export interface CurrentUser {
  id: string;
  email: string;
  phone_number?: string | null;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  settings: UserSettings;
  created_at: string;
  updated_at: string | null;
}

