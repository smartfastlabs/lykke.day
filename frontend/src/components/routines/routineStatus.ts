import type { TimingStatus } from "@/types/api";

export type RoutineCompletionState = "complete" | "punted" | "normal";

export function getRoutineCompletionState(input: {
  totalCount: number;
  completedCount: number;
  puntedCount: number;
}): RoutineCompletionState {
  if (input.totalCount > 0 && input.completedCount === input.totalCount) {
    return "complete";
  }
  if (input.totalCount > 0 && input.puntedCount === input.totalCount) {
    return "punted";
  }
  return "normal";
}

const defaultFormatTime = (date: Date): string =>
  date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

/**
 * Label shown in the routine "status pill".
 *
 * Important:
 * - `completionState` overrides timing status (protects against stale timing_status
 *   when everything is complete/punted).
 */
export function getRoutineStatusLabel(input: {
  completionState: RoutineCompletionState;
  timingStatus: TimingStatus | null | undefined;
  nextAvailableTime: Date | null;
  formatTime?: (date: Date) => string;
}): string {
  if (input.completionState === "complete") return "Done";
  if (input.completionState === "punted") return "Punted";

  const status: TimingStatus = input.timingStatus ?? "hidden";
  const formatTime = input.formatTime ?? defaultFormatTime;

  if (status === "active") return "Active";
  if (status === "available") return "Available";
  if (status === "needs_attention") return "Due soon";
  if (status === "past-due") return "Past due";

  if (status === "inactive") {
    if (input.nextAvailableTime)
      return `Starts ${formatTime(input.nextAvailableTime)}`;
    return "Soon";
  }

  // hidden
  if (input.nextAvailableTime)
    return `Starts ${formatTime(input.nextAvailableTime)}`;
  return "Later";
}

/**
 * Tailwind classes for routine "status pill".
 *
 * Completion state overrides timing status for consistency with the card colors.
 */
export function getRoutineStatusPillClass(input: {
  completionState: RoutineCompletionState;
  timingStatus: TimingStatus | null | undefined;
}): string {
  if (input.completionState === "complete") {
    return "bg-emerald-100/70 text-emerald-700";
  }
  if (input.completionState === "punted") {
    return "bg-rose-100/80 text-rose-700";
  }

  const status: TimingStatus = input.timingStatus ?? "hidden";

  if (status === "active") return "bg-emerald-100/70 text-emerald-700";
  if (status === "available") return "bg-amber-100/80 text-amber-700";
  if (status === "needs_attention") return "bg-amber-100/80 text-amber-700";
  if (status === "past-due") return "bg-rose-100/80 text-rose-700";
  if (status === "inactive") return "bg-stone-100 text-stone-600";
  return "bg-stone-100 text-stone-600";
}
