export type FactoidType = "episodic" | "semantic" | "procedural";
export type FactoidCriticality = "normal" | "important" | "critical";

export type Factoid = {
  id?: string | null;
  user_id?: string;
  factoid_type: FactoidType;
  criticality: FactoidCriticality;
  content: string;
  embedding?: number[] | null;
  ai_suggested?: boolean;
  user_confirmed?: boolean;
  last_accessed?: string;
  access_count?: number;
  meta?: Record<string, unknown>;
  created_at?: string;
};
