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
  entity_patch?: JsonPatchOp[] | null;
}

export interface JsonPatchOp {
  op: "replace" | "add" | "remove";
  path: string;
  value?: unknown;
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

const cloneValue = <T>(value: T): T => {
  if (typeof structuredClone === "function") {
    return structuredClone(value);
  }
  return JSON.parse(JSON.stringify(value)) as T;
};

const decodePointer = (path: string): string[] => {
  if (path === "" || path === "/") return [];
  const trimmed = path.startsWith("/") ? path.slice(1) : path;
  if (!trimmed) return [];
  return trimmed.split("/").map((segment) =>
    segment.replace(/~1/g, "/").replace(/~0/g, "~"),
  );
};

const setValueAtPath = (
  target: unknown,
  segments: string[],
  value: unknown,
): unknown => {
  if (segments.length === 0) {
    return value;
  }
  const next = Array.isArray(target) ? [...target] : { ...(target as object) };
  let cursor: unknown = next;
  for (let i = 0; i < segments.length - 1; i += 1) {
    const segment = segments[i];
    const index =
      Array.isArray(cursor) && /^\d+$/.test(segment)
        ? Number(segment)
        : null;
    if (Array.isArray(cursor)) {
      if (index === null) return next;
      if (cursor[index] === undefined) {
        cursor[index] = {};
      }
      cursor = cursor[index];
    } else if (typeof cursor === "object" && cursor !== null) {
      const record = cursor as Record<string, unknown>;
      if (record[segment] === undefined || record[segment] === null) {
        record[segment] = {};
      }
      cursor = record[segment];
    } else {
      return next;
    }
  }

  const last = segments[segments.length - 1];
  const lastIndex =
    Array.isArray(cursor) && /^\d+$/.test(last) ? Number(last) : null;
  if (Array.isArray(cursor) && lastIndex !== null) {
    cursor[lastIndex] = value;
  } else if (typeof cursor === "object" && cursor !== null) {
    (cursor as Record<string, unknown>)[last] = value;
  }

  return next;
};

export const applyEntityPatch = <T>(
  current: T,
  patch: JsonPatchOp[],
): T => {
  let next = cloneValue(current);
  for (const op of patch) {
    const segments = decodePointer(op.path);
    if (op.op === "remove") {
      continue;
    }
    next = setValueAtPath(next, segments, op.value) as T;
  }
  return next;
};

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

      if (change.entity_patch && change.entity_patch.length > 0) {
        const index = updatedTasks.findIndex((t) => t.id === change.entity_id);
        const base = index >= 0 ? updatedTasks[index] : ({} as Task);
        const patched = applyEntityPatch(base, change.entity_patch) as Task;
        if (!patched || !patched.id) continue;
        if (index >= 0) {
          if (!areEntitiesEqual(updatedTasks[index], patched)) {
            updatedTasks[index] = patched;
            didUpdate = true;
          }
        } else {
          updatedTasks.push(patched);
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

      if (change.entity_patch && change.entity_patch.length > 0) {
        const index = updatedEvents.findIndex((e) => e.id === change.entity_id);
        const base = index >= 0 ? updatedEvents[index] : ({} as Event);
        const patched = applyEntityPatch(base, change.entity_patch) as Event;
        if (!patched || !patched.id) continue;
        if (index >= 0) {
          if (!areEntitiesEqual(updatedEvents[index], patched)) {
            updatedEvents[index] = patched;
            didUpdate = true;
          }
        } else {
          updatedEvents.push(patched);
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

      if (change.entity_patch && change.entity_patch.length > 0) {
        const index = updatedRoutines.findIndex((r) => r.id === change.entity_id);
        const base = index >= 0 ? updatedRoutines[index] : ({} as Routine);
        const patched = applyEntityPatch(base, change.entity_patch) as Routine;
        if (!patched || !patched.id) continue;
        if (index >= 0) {
          if (!areEntitiesEqual(updatedRoutines[index], patched)) {
            updatedRoutines[index] = patched;
            didUpdate = true;
          }
        } else {
          updatedRoutines.push(patched);
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
      if (change.entity_patch && change.entity_patch.length > 0) {
        const base = (next.day ?? ({} as Day)) as Day;
        const patched = applyEntityPatch(base, change.entity_patch) as Day;
        if (patched && !areEntitiesEqual(next.day, patched)) {
          next.day = patched;
          didUpdate = true;
        }
      } else {
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
  }

  if (!didUpdate) {
    return { didUpdate: false, nextContext: current };
  }

  next.tasks = updatedTasks;
  next.calendar_entries = updatedEvents;
  next.routines = updatedRoutines;

  return { didUpdate: true, nextContext: next };
};
