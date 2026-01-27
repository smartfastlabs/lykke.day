import type { Task, TimingStatus } from "@/types/api";

export function getTaskNextAvailableTime(task: Task): Date | null {
  if (!task.next_available_time) return null;
  const parsed = new Date(task.next_available_time);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function isTaskTimingStatus(task: Task, status: TimingStatus): boolean {
  return task.timing_status === status;
}

export function isTaskAvailable(task: Task): boolean {
  return task.timing_status === "available" || task.timing_status === "active";
}

export function filterVisibleTasks(tasks: Task[]): Task[] {
  return tasks.filter((task) => task.timing_status !== "hidden");
}
