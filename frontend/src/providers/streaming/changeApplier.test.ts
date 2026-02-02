import { describe, it, expect } from "vitest";

import { applyEntityChanges, type EntityChange } from "./changeApplier";
import type { Task } from "@/types/api";

describe("applyEntityChanges", () => {
  it("applies created/updated/deleted task changes without mutating input", () => {
    const original = {
      day: { id: "day-1" },
      tasks: [{ id: "t-1", status: "NOT_STARTED", name: "Old" }],
      calendar_entries: [],
      routines: [],
    } as unknown as import("@/types/api").DayContextWithRoutines;

    const snapshot = JSON.parse(JSON.stringify(original)) as typeof original;

    const changes: EntityChange[] = [
      {
        change_type: "created",
        entity_type: "task",
        entity_id: "t-2",
        entity_data: {
          id: "t-2",
          status: "NOT_STARTED",
          name: "New",
        } as unknown as Task,
      },
      {
        change_type: "updated",
        entity_type: "task",
        entity_id: "t-1",
        entity_data: {
          id: "t-1",
          status: "COMPLETE",
          name: "Old",
        } as unknown as Task,
      },
      {
        change_type: "deleted",
        entity_type: "task",
        entity_id: "t-2",
        entity_data: null,
      },
    ];

    const result = applyEntityChanges(original, changes);
    expect(result.didUpdate).toBe(true);
    expect(result.nextContext.tasks?.map((t) => t.id)).toEqual(["t-1"]);
    expect(result.nextContext.tasks?.[0]?.status).toBe("COMPLETE");

    // Input was not mutated.
    expect(original).toEqual(snapshot);
  });

  it("returns didUpdate=false and preserves reference when nothing changes", () => {
    const original = {
      day: { id: "day-1" },
      tasks: [{ id: "t-1", status: "NOT_STARTED", name: "Same" }],
      calendar_entries: [],
      routines: [],
    } as unknown as import("@/types/api").DayContextWithRoutines;

    const changes: EntityChange[] = [
      {
        change_type: "updated",
        entity_type: "task",
        entity_id: "t-1",
        entity_data: {
          id: "t-1",
          status: "NOT_STARTED",
          name: "Same",
        } as unknown as Task,
      },
    ];

    const result = applyEntityChanges(original, changes);
    expect(result.didUpdate).toBe(false);
    expect(result.nextContext).toBe(original);
  });

  it("applies JSON Patch updates for tasks", () => {
    const original = {
      day: { id: "day-1" },
      tasks: [{ id: "t-1", status: "NOT_STARTED", name: "Same" }],
      calendar_entries: [],
      routines: [],
    } as unknown as import("@/types/api").DayContextWithRoutines;

    const changes: EntityChange[] = [
      {
        change_type: "updated",
        entity_type: "task",
        entity_id: "t-1",
        entity_data: null,
        entity_patch: [
          { op: "replace", path: "/status", value: "COMPLETE" },
        ],
      },
    ];

    const result = applyEntityChanges(original, changes);
    expect(result.didUpdate).toBe(true);
    expect(result.nextContext.tasks?.[0]?.status).toBe("COMPLETE");
  });
});
