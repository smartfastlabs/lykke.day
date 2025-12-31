import { TaskStatus, TaskType, TaskFrequency } from "../../../types/api";

// Filter constants
export const ALL_STATUSES: TaskStatus[] = [
  "READY",
  "COMPLETE",
  "NOT_READY",
  "PUNT",
  "NOT_STARTED",
  "PENDING",
];

export const ALL_TYPES: TaskType[] = ["MEAL", "EVENT", "CHORE", "ERRAND", "ACTIVITY"];

export const ALL_FREQUENCIES: TaskFrequency[] = [
  "DAILY",
  "WEEKLY",
  "BI_WEEKLY",
  "MONTHLY",
  "YEARLY",
  "ONCE",
  "WORK_DAYS",
  "WEEKENDS",
  "CUSTOM_WEEKLY",
];

// Frequency display groups for the simplified filter
export type FrequencyGroup = "ONCE" | "DAILY" | "WEEKLY" | "MONTHLY+";

export const FREQUENCY_GROUPS: FrequencyGroup[] = [
  "ONCE",
  "DAILY",
  "WEEKLY",
  "MONTHLY+",
];

// Map frequency groups to actual TaskFrequency values
export const frequencyGroupMap: Record<FrequencyGroup, TaskFrequency[]> = {
  ONCE: ["ONCE"],
  DAILY: ["DAILY", "WORK_DAYS", "WEEKENDS"],
  WEEKLY: ["WEEKLY", "BI_WEEKLY", "CUSTOM_WEEKLY"],
  "MONTHLY+": ["MONTHLY", "YEARLY"],
};

// Filter state interface
export interface TaskFiltersState {
  statuses: TaskStatus[];
  types: TaskType[];
  frequencyGroups: FrequencyGroup[];
}

// Helper to format labels
export const formatLabel = (str: string): string =>
  str
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

