import type { components } from "./api.generated";

export type Routine = components["schemas"]["RoutineSchema"];

export type RoutineSummary = Routine;

export type DayContextWithRoutines = components["schemas"]["DayContextSchema"] & {
  routines?: Routine[];
};
