import { TaskStatusType, Task, TaskStatus, Day } from "..types/tasks";

import { TaskStorage } from "../utils/localStorage/tasks";
import { getDateString, getTime, getDayOfWeek } from "../utils/dates";
import { dayAPI } from "../utils/api";

const TaskService = {
  getTasksForDate: async (date?: string | null): Promise<Task[]> => {
    if (!date) {
      date = getDateString();
    }
    const existingTasks = TaskStorage.getTasks(date);

    if (existingTasks) {
      console.log("Date already Scheduled", date);
      return existingTasks;
    }

    return TaskService.scheduleToday();
  },

  setTaskStatus: async (task: Task, status: TaskStatusType): Promise<Task> => {
    console.log(task);
    task.statuses.push({
      type: status,
      createdAt: new Date(),
    });

    TaskStorage.saveTask(task);
    return task;
  },

  scheduleToday: async (): Promise<Task[]> => {
    console.log("Scheduling Date");

    const day: Day = await dayAPI.scheduleToday();
    for (const task of day.tasks) {
      console.log(task);
    }

    TaskStorage.saveTasks(day.date, day.tasks);

    return day.tasks;
  },
};

export default TaskService;
