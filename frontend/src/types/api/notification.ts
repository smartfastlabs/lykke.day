import type { components } from "./api.generated";
import type { Routine } from "./routine";

export type LLMRunResultSnapshot = {
  current_time?: string;
  llm_provider?: string;
  system_prompt?: string;
  referenced_entities?: { entity_type: string; entity_id: string }[];
  messages?: { role: string; content: string | unknown }[];
  tools?: Record<string, unknown>[];
  tool_choice?: unknown;
  model_params?: Record<string, unknown>;
};

export type ReferencedEntity = { entity_type: string; entity_id: string };

export type Task = components["schemas"]["TaskSchema"];
export type Event = components["schemas"]["CalendarEntrySchema"];

export type PushNotification = {
  id?: string | null;
  user_id: string;
  push_subscription_ids: string[];
  content: string;
  status: string;
  error_message?: string | null;
  sent_at: string;
  message?: string | null;
  priority?: string | null;
  message_hash?: string | null;
  triggered_by?: string | null;
  llm_snapshot?: LLMRunResultSnapshot | Record<string, unknown> | null;
  referenced_entities?: ReferencedEntity[];
};

export type PushNotificationContext = {
  notification: PushNotification;
  tasks: Task[];
  routines: Routine[];
  calendar_entries: Event[];
};
