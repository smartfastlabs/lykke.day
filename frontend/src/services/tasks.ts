import { TaskStatusType, Task, TaskStatus } from "..types/tasks";

import { TaskStorage } from "../utils/localStorage/tasks";
import { getDateString, getTime, getDayOfWeek } from "../utils/dates";

import { exampleTasks } from "../data/dailyTasks";

const TaskService = {
  getTasksForDate: (date?: string | null) => {
    if (!date) {
      date = getDateString();
    }
    const existingTasks = TaskStorage.getTasks(date);

    if (existingTasks) {
      console.log("Date already Scheduled", date);
      return existingTasks;
    }

    return TaskService.scheduleTasksForDate(date);
  },

  setTaskStatus: (task: Task, status: TaskStatusType): Task => {
    console.log(task);
    task.statuses.push({
      type: status,
      createdAt: new Date(),
    });

    TaskStorage.saveTask(task);
    return task;
  },

  scheduleTasksForDate: (date?: string | null): Task[] => {
    if (!date) {
      date = getDateString();
    }

    console.log("Scheduling Date", date);
    const tasks: Task[] = [];

    for (const task of exampleTasks) {
      if (task.frequency == "CUSTOM_WEEKLY") {
        if (!task.scheduleDays?.includes(getDayOfWeek())) {
          continue;
        }
      }

      tasks.push({
        definition: task,
        date: date,
        statuses: [],
      } as Task);
    }

    TaskStorage.saveTasks(date, tasks);

    return tasks;
  },
};

export default TaskService;
