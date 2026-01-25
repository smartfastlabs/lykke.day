import type { components } from "./api.generated";

export type Routine = {
  id?: string | null;
  user_id: string;
  date: string;
  routine_definition_id: string;
  name: string;
  category: components["schemas"]["TaskCategory"];
  description: string;
  time_window?: components["schemas"]["TimeWindowSchema"] | null;
};

export type RoutineSummary = Routine;

export type DayContextWithRoutines = components["schemas"]["DayContextSchema"] & {
  routines?: Routine[];
};
