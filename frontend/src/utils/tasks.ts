import { getTime } from "./dates";
import type { Task } from "@/types/api";

interface GroupedTasks {
  punted: Task[];
  pending: Task[];
  missed: Task[];
  completed: Task[];
}

export function isTaskSnoozed(task: Task, now: Date = new Date()): boolean {
  if (!task.snoozed_until) return false;
  const snoozedUntil = new Date(task.snoozed_until);
  return snoozedUntil > now;
}

export function filterVisibleTasks(
  tasks: Task[],
  now: Date = new Date()
): Task[] {
  return tasks.filter((task) => !isTaskSnoozed(task, now));
}

export function groupTasks(tasks: Task[]): GroupedTasks {
  // remove all items with availableTime in the future
  const result: GroupedTasks = {
    punted: [],
    pending: [],
    missed: [],
    completed: [],
  };
  const now = new Date();

  for (const task of tasks) {
    if (isTaskSnoozed(task, now)) {
      continue;
    }
    const taskDate = task.scheduled_date;
    if (!taskDate) {
      // If no date is available, treat as pending and skip time-based logic
      result.pending.push(task);
      continue;
    }

    const timeWindow = task.time_window;
    if (!timeWindow) {
      result.pending.push(task);
      continue;
    }

    const startTime: Date | null = timeWindow.start_time
      ? getTime(taskDate, timeWindow.start_time)
      : null;

    const endTime: Date | null = timeWindow.end_time
      ? getTime(taskDate, timeWindow.end_time)
      : null;

    const availableTime: Date | null = timeWindow.available_time
      ? getTime(taskDate, timeWindow.available_time)
      : null;

    const taskStatus = task.status;

    // Infer timing behavior from field presence
    // start_time + end_time => time window
    // start_time only => fixed time
    // end_time only => deadline
    // available_time only => flexible
    // multiple fields => use most specific behavior

    if (taskStatus === "COMPLETE") {
      result.completed.push(task);
    } else if (taskStatus === "PUNT") {
      result.punted.push(task);
    } else if (startTime && !endTime) {
      // Fixed time: start_time only
      if (startTime < new Date()) {
        result.missed.push(task);
      } else {
        result.pending.push(task);
      }
    } else if (endTime && !startTime) {
      // Deadline: end_time only
      if (endTime < new Date()) {
        result.missed.push(task);
      } else if (!availableTime || availableTime < new Date()) {
        result.pending.push(task);
      }
    } else if (startTime && endTime) {
      // Time window: both start and end
      result.pending.push(task);
    } else if (availableTime) {
      // Flexible: available_time only
      if (availableTime < new Date()) {
        result.pending.push(task);
      }
    } else {
      // No time fields set
      result.pending.push(task);
    }
  }

  return result;
}
