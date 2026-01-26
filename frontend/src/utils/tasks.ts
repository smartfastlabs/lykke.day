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

export function getTaskAvailableTime(task: Task): Date | null {
  const taskDate = task.scheduled_date;
  const timeWindow = task.time_window;
  if (!taskDate || !timeWindow?.available_time) return null;
  return getTime(taskDate, timeWindow.available_time);
}

export function getTaskDueByTime(task: Task): Date | null {
  const taskDate = task.scheduled_date;
  const timeWindow = task.time_window;
  if (!taskDate || !timeWindow) return null;
  const dueBy = timeWindow.cutoff_time ?? timeWindow.end_time;
  if (!dueBy) return null;
  return getTime(taskDate, dueBy);
}

export function getTaskUpcomingTime(
  task: Task,
  now: Date = new Date(),
): Date | null {
  const taskDate = task.scheduled_date;
  const timeWindow = task.time_window;
  if (!taskDate || !timeWindow) return null;

  const availableTime = getTaskAvailableTime(task);
  const dueByTime = getTaskDueByTime(task);

  if (availableTime && availableTime <= now && dueByTime) {
    return dueByTime;
  }

  // Prefer start_time for fixed time tasks
  if (timeWindow.start_time && !timeWindow.end_time) {
    return getTime(taskDate, timeWindow.start_time);
  }

  // Use end_time for deadline tasks
  if (timeWindow.end_time && !timeWindow.start_time) {
    return getTime(taskDate, timeWindow.end_time);
  }

  // For time windows, use start_time
  if (timeWindow.start_time) {
    return getTime(taskDate, timeWindow.start_time);
  }

  // Fallback to available_time
  if (timeWindow.available_time) {
    return getTime(taskDate, timeWindow.available_time);
  }

  // Final fallback to cutoff/end time
  if (timeWindow.cutoff_time) {
    return getTime(taskDate, timeWindow.cutoff_time);
  }

  return null;
}

export function isTaskAvailable(
  task: Task,
  now: Date = new Date(),
  windowMinutes: number = 30,
): boolean {
  if (task.status === "COMPLETE" || task.status === "PUNT") {
    return false;
  }
  if (isTaskSnoozed(task, now)) {
    return false;
  }

  const availableTime = getTaskAvailableTime(task);
  if (!availableTime || availableTime > now) {
    return false;
  }

  const dueByTime = getTaskDueByTime(task);
  if (!dueByTime) {
    return true;
  }

  const windowEnd = new Date(now.getTime() + 1000 * 60 * windowMinutes);
  if (dueByTime <= now) {
    return false;
  }

  return dueByTime > windowEnd;
}

export function filterVisibleTasks(
  tasks: Task[],
  now: Date = new Date(),
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
