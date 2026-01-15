import { getTime } from "./dates";
import type { Task } from "@/types/api";

interface GroupedTasks {
  punted: Task[];
  pending: Task[];
  missed: Task[];
  completed: Task[];
}

export function groupTasks(tasks: Task[]): GroupedTasks {
  // remove all items with availableTime in the future
  const result: GroupedTasks = {
    punted: [],
    pending: [],
    missed: [],
    completed: [],
  };

  for (const task of tasks) {
    const taskDate = task.scheduled_date;
    if (!taskDate) {
      // If no date is available, treat as pending and skip time-based logic
      result.pending.push(task);
      continue;
    }

    const schedule = task.schedule;
    if (!schedule) {
      result.pending.push(task);
      continue;
    }

    const startTime: Date | null = schedule.start_time
      ? getTime(taskDate, schedule.start_time)
      : null;

    const endTime: Date | null = schedule.end_time
      ? getTime(taskDate, schedule.end_time)
      : null;

    const availableTime: Date | null = schedule.available_time
      ? getTime(taskDate, schedule.available_time)
      : null;

    const taskStatus = task.status;

    switch (schedule.timing_type) {
      case "FIXED_TIME":
        if (taskStatus === "COMPLETE") {
          result.completed.push(task);
        } else if (taskStatus === "PUNT") {
          result.punted.push(task);
        } else if (startTime && startTime < new Date()) {
          result.missed.push(task);
        } else {
          result.pending.push(task);
        }
        break;
      case "DEADLINE":
        if (taskStatus === "COMPLETE") {
          result.completed.push(task);
        } else if (taskStatus === "PUNT") {
          result.punted.push(task);
        } else if (endTime && endTime < new Date()) {
          result.missed.push(task);
        } else if (!availableTime || availableTime < new Date()) {
          result.pending.push(task);
        }
        break;
      case "TIME_WINDOW":
        if (taskStatus === "COMPLETE") {
          result.completed.push(task);
        } else if (taskStatus === "PUNT") {
          result.punted.push(task);
        } else {
          result.pending.push(task);
        }
        break;
      case "FLEXIBLE":
        if (taskStatus === "COMPLETE") {
          result.completed.push(task);
        } else if (taskStatus === "PUNT") {
          result.punted.push(task);
        } else if (!availableTime || availableTime < new Date()) {
          result.pending.push(task);
        }
        break;
    }
  }

  return result;
}
