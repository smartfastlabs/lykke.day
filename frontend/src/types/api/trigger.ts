export type Trigger = {
  id?: string | null;
  user_id?: string;
  name: string;
  description: string;
};

export type TriggerTacticsUpdate = {
  tactic_ids: string[];
};
