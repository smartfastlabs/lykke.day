export type LLMToolCallResultSnapshot = {
  tool_name: string;
  arguments?: Record<string, unknown>;
  result?: unknown;
};

export type LLMRunResultSnapshot = {
  tool_calls?: LLMToolCallResultSnapshot[];
  prompt_context?: Record<string, unknown>;
  current_time?: string;
  llm_provider?: string;
  system_prompt?: string;
  context_prompt?: string;
  ask_prompt?: string;
  tools_prompt?: string;
  referenced_entities?: { entity_type: string; entity_id: string }[];
};

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
};
