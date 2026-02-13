/**
 * Shared utilities for notification detail views.
 */

export const safeStringify = (value: unknown): string => {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
};

export const parseContent = (content: string): Record<string, unknown> | null => {
  try {
    const parsed = JSON.parse(content);
    if (parsed && typeof parsed === "object") {
      return parsed as Record<string, unknown>;
    }
  } catch {
    return null;
  }
  return null;
};

export const formatNotificationDateTime = (value: string): string => {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

/**
 * Map entity_type to a human-readable label.
 */
export const getEntityTypeLabel = (entityType: string): string => {
  const labels: Record<string, string> = {
    task: "Task",
    calendar_entry: "Event",
    calendarentry: "Event",
    routine: "Routine",
    day: "Day",
    brain_dump: "Brain dump",
    routine_definition: "Routine definition",
  };
  return labels[entityType] ?? entityType.replace(/_/g, " ");
};
