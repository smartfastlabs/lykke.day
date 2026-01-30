import type {
  Day,
  DayContextWithRoutines,
  Event,
  Routine,
  Task,
} from "@/types/api";

export interface EntityChange {
  change_type: "created" | "updated" | "deleted";
  entity_type: string;
  entity_id: string;
  entity_data: Task | Event | Routine | Day | null;
}

const stableStringify = (value: unknown): string => {
  if (value === null || value === undefined) {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(",")}]`;
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const keys = Object.keys(record).sort();
    return `{${keys
      .map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
};

const areEntitiesEqual = (left: unknown, right: unknown): boolean =>
  stableStringify(left) === stableStringify(right);

export interface ApplyEntityChangesResult {
  didUpdate: boolean;
  nextContext: DayContextWithRoutines;
}

/**
 * Apply incremental entity changes to an in-memory `DayContextWithRoutines`.
 * This function is intentionally pure to keep the provider small and focused.
 */
export const applyEntityChanges = (
  current: DayContextWithRoutines,
  changes: EntityChange[],
): ApplyEntityChangesResult => {
  let didUpdate = false;

  const next: DayContextWithRoutines = { ...current };
  const updatedTasks = [...(next.tasks ?? [])];
  const updatedEvents = [...(next.calendar_entries ?? [])];
  const updatedRoutines = [...(next.routines ?? [])];

  for (const change of changes) {
    if (change.entity_type === "task") {
      if (change.change_type === "deleted") {
        const index = updatedTasks.findIndex((t) => t.id === change.entity_id);
        if (index >= 0) {
          updatedTasks.splice(index, 1);
          didUpdate = true;
        }
        continue;
      }

      const task = change.entity_data as Task | null;
      if (!task) continue;

      const index = updatedTasks.findIndex((t) => t.id === task.id);
      if (index >= 0) {
        if (!areEntitiesEqual(updatedTasks[index], task)) {
          updatedTasks[index] = task;
          didUpdate = true;
        }
      } else {
        updatedTasks.push(task);
        didUpdate = true;
      }

      continue;
    }

    if (
      change.entity_type === "calendar_entry" ||
      change.entity_type === "calendarentry"
    ) {
      if (change.change_type === "deleted") {
        const index = updatedEvents.findIndex((e) => e.id === change.entity_id);
        if (index >= 0) {
          updatedEvents.splice(index, 1);
          didUpdate = true;
        }
        continue;
      }

      const event = change.entity_data as Event | null;
      if (!event) continue;

      const index = updatedEvents.findIndex((e) => e.id === event.id);
      if (index >= 0) {
        if (!areEntitiesEqual(updatedEvents[index], event)) {
          updatedEvents[index] = event;
          didUpdate = true;
        }
      } else {
        updatedEvents.push(event);
        didUpdate = true;
      }

      continue;
    }

    if (change.entity_type === "routine") {
      if (change.change_type === "deleted") {
        const index = updatedRoutines.findIndex(
          (r) => r.id === change.entity_id,
        );
        if (index >= 0) {
          updatedRoutines.splice(index, 1);
          didUpdate = true;
        }
        continue;
      }

      const routine = change.entity_data as Routine | null;
      if (!routine) continue;

      const index = updatedRoutines.findIndex((r) => r.id === routine.id);
      if (index >= 0) {
        if (!areEntitiesEqual(updatedRoutines[index], routine)) {
          updatedRoutines[index] = routine;
          didUpdate = true;
        }
      } else {
        updatedRoutines.push(routine);
        didUpdate = true;
      }

      continue;
    }

    if (change.entity_type === "day") {
      const updatedDay = change.entity_data as Day | null;
      if (
        updatedDay &&
        (change.change_type === "updated" || change.change_type === "created")
      ) {
        if (!areEntitiesEqual(next.day, updatedDay)) {
          next.day = updatedDay;
          didUpdate = true;
        }
      }
    }
  }

  if (!didUpdate) {
    return { didUpdate: false, nextContext: current };
  }

  next.tasks = updatedTasks;
  next.calendar_entries = updatedEvents;
  next.routines = updatedRoutines;

  return { didUpdate: true, nextContext: next };
};
