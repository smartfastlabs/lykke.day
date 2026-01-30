import { describe, it, expect } from "vitest";

import {
  buildChangeNotification,
  buildTaskCompletedNotification,
  countCompletedTasksFromChanges,
  countCompletedTasksFromFullSync,
} from "./notifications";

import type { Day, DayContextWithRoutines, Routine, Task } from "@/types/api";
import type { EntityChange } from "./changeApplier";

describe("streaming notifications helpers", () => {
  it("buildChangeNotification returns null for no changes", () => {
    expect(buildChangeNotification([])).toBeNull();
  });

  it("buildChangeNotification summarizes up to 3 change groups", () => {
    const changes: EntityChange[] = [
      {
        change_type: "updated",
        entity_type: "task",
        entity_id: "t-1",
        entity_data: { id: "t-1" } as unknown as Task,
      },
      {
        change_type: "updated",
        entity_type: "task",
        entity_id: "t-2",
        entity_data: { id: "t-2" } as unknown as Task,
      },
      {
        change_type: "deleted",
        entity_type: "calendar_entry",
        entity_id: "e-1",
        entity_data: null,
      },
      {
        change_type: "created",
        entity_type: "routine",
        entity_id: "r-1",
        entity_data: { id: "r-1" } as unknown as Routine,
      },
    ];

    const message = buildChangeNotification(changes);
    expect(message).toContain("Background update:");
    expect(message).toContain("2 tasks updated");
    expect(message).toContain("1 event removed");
    expect(message).toContain("1 routine added");
    // 3 groups max; we gave exactly 3 unique groups, so no suffix
    expect(message).not.toContain("more updates");
  });

  it("buildChangeNotification adds suffix when more than 3 groups", () => {
    const changes: EntityChange[] = [
      {
        change_type: "created",
        entity_type: "task",
        entity_id: "t-1",
        entity_data: { id: "t-1" } as unknown as Task,
      },
      {
        change_type: "updated",
        entity_type: "routine",
        entity_id: "r-1",
        entity_data: { id: "r-1" } as unknown as Routine,
      },
      {
        change_type: "deleted",
        entity_type: "calendar_entry",
        entity_id: "e-1",
        entity_data: null,
      },
      {
        change_type: "updated",
        entity_type: "day",
        entity_id: "d-1",
        entity_data: { id: "d-1" } as unknown as Day,
      },
    ];

    const message = buildChangeNotification(changes);
    expect(message).toContain("and 1 more updates");
  });

  it("counts completed tasks from incremental changes", () => {
    const current: DayContextWithRoutines = {
      day: { id: "d-1" } as unknown as Day,
      tasks: [{ id: "t-1", status: "NOT_STARTED" } as unknown as Task],
      calendar_entries: [],
      routines: [],
    } as unknown as DayContextWithRoutines;

    const changes: EntityChange[] = [
      {
        change_type: "updated",
        entity_type: "task",
        entity_id: "t-1",
        entity_data: { id: "t-1", status: "COMPLETE" } as unknown as Task,
      },
    ];

    expect(countCompletedTasksFromChanges(current, changes)).toBe(1);
    expect(buildTaskCompletedNotification(1)).toBe(
      "Background update: 1 task completed.",
    );
  });

  it("counts completed tasks from full sync", () => {
    const previous = [{ id: "t-1", status: "NOT_STARTED" } as unknown as Task];
    const next = [{ id: "t-1", status: "COMPLETE" } as unknown as Task];
    expect(countCompletedTasksFromFullSync(previous, next)).toBe(1);
    expect(buildTaskCompletedNotification(2)).toBe(
      "Background update: 2 tasks completed.",
    );
  });
});
