import type { DayContextWithRoutines, Task } from "@/types/api";

import type { EntityChange } from "./changeApplier";

const getEntityLabel = (entityType: string): string => {
  if (entityType === "calendar_entry" || entityType === "calendarentry") {
    return "event";
  }
  if (entityType === "task") return "task";
  if (entityType === "routine") return "routine";
  if (entityType === "day") return "day";
  return entityType.replace(/_/g, " ");
};

const getChangeVerb = (changeType: EntityChange["change_type"]): string => {
  if (changeType === "created") return "added";
  if (changeType === "updated") return "updated";
  return "removed";
};

const pluralize = (count: number, noun: string): string =>
  count === 1 ? noun : `${noun}s`;

export const buildChangeNotification = (
  changes: EntityChange[],
): string | null => {
  if (changes.length === 0) return null;

  const counts = new Map<string, number>();

  for (const change of changes) {
    const key = `${getEntityLabel(change.entity_type)}|${getChangeVerb(
      change.change_type,
    )}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const parts = Array.from(counts.entries()).map(([key, count]) => {
    const [entityLabel, changeVerb] = key.split("|");
    return `${count} ${pluralize(count, entityLabel)} ${changeVerb}`;
  });

  if (parts.length === 0) return null;

  const maxParts = 3;
  const shownParts = parts.slice(0, maxParts);
  const remaining = parts.length - shownParts.length;
  const suffix = remaining > 0 ? `, and ${remaining} more updates` : "";

  return `Background update: ${shownParts.join(", ")}${suffix}.`;
};

export const countCompletedTasksFromChanges = (
  current: DayContextWithRoutines,
  changes: EntityChange[],
): number => {
  const existingTasks = current.tasks ?? [];
  let completedCount = 0;

  for (const change of changes) {
    if (change.entity_type !== "task") continue;
    if (change.change_type !== "updated") continue;
    const task = change.entity_data as Task | null;
    if (!task || !task.id) continue;
    const previous = existingTasks.find((existing) => existing.id === task.id);
    if (previous?.status !== "COMPLETE" && task.status === "COMPLETE") {
      completedCount += 1;
    }
  }

  return completedCount;
};

export const countCompletedTasksFromFullSync = (
  previousTasks: Task[],
  nextTasks: Task[],
): number => {
  const previousById = new Map(previousTasks.map((task) => [task.id, task]));
  let completedCount = 0;

  for (const task of nextTasks) {
    const previous = task.id ? previousById.get(task.id) : undefined;
    if (previous?.status !== "COMPLETE" && task.status === "COMPLETE") {
      completedCount += 1;
    }
  }

  return completedCount;
};

export const buildTaskCompletedNotification = (count: number): string =>
  count === 1
    ? "Background update: 1 task completed."
    : `Background update: ${count} tasks completed.`;
