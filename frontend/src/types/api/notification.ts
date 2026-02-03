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
