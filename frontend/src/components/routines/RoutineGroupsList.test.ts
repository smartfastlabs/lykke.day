import { describe, expect, it } from "vitest";
import { buildRoutineGroups } from "@/components/routines/RoutineGroupsList";
import type { Routine, Task } from "@/types/api";

describe("buildRoutineGroups", () => {
  it("builds groups using routines metadata and task counts", () => {
    const routines: Routine[] = [
      {
        id: "r-1",
        routine_definition_id: "rd-1",
        name: "Morning Routine",
        timing_status: "active",
        next_available_time: null,
      } as unknown as Routine,
    ];

    const tasks: Task[] = [
      {
        id: "t-1",
        routine_definition_id: "rd-1",
        status: "COMPLETE",
      } as unknown as Task,
      {
        id: "t-2",
        routine_definition_id: "rd-1",
        status: "PUNT",
      } as unknown as Task,
      {
        id: "t-3",
        routine_definition_id: "rd-1",
        status: "NOT_STARTED",
      } as unknown as Task,
      // Should be ignored (not part of any routine group).
      { id: "t-4", status: "NOT_STARTED" } as unknown as Task,
    ];

    const groups = buildRoutineGroups(tasks, routines);
    expect(groups).toHaveLength(1);
    expect(groups[0]).toMatchObject({
      routineId: "r-1",
      routineDefinitionId: "rd-1",
      routineName: "Morning Routine",
      totalCount: 3,
      completedCount: 1,
      puntedCount: 1,
      pendingCount: 1,
      timing_status: "active",
      next_available_time: null,
    });
  });

  it("creates fallback groups for routine-linked tasks without a routine entity", () => {
    const routines: Routine[] = [];
    const tasks: Task[] = [
      {
        id: "t-1",
        routine_definition_id: "rd-missing",
        status: "NOT_STARTED",
      } as unknown as Task,
    ];

    const groups = buildRoutineGroups(tasks, routines);
    expect(groups).toHaveLength(1);
    expect(groups[0]).toMatchObject({
      routineId: null,
      routineDefinitionId: "rd-missing",
      routineName: "Routine",
      totalCount: 1,
      completedCount: 0,
      puntedCount: 0,
      pendingCount: 1,
      timing_status: null,
      next_available_time: null,
    });
  });
});
