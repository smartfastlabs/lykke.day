import { Task } from "../types/api";

const TASK_KEY = (d: string): string => `tasks.instances.${d}`;

function getFromStorage<T>(key: string): T | null {
  const result = localStorage.getItem(key);
  if (!result) return null;
  return JSON.parse(result) as T;
}

function saveToStorage<T>(key: string, value: T): void {
  localStorage.setItem(key, JSON.stringify(value));
}

const getTasksFromStorage = getFromStorage<Task[]>;

// ---- Core Storage API ----
export const TaskStorage = {
  saveTasks(date: string, tasks: Task[]) {
    saveToStorage(TASK_KEY(date), tasks);
  },

  getTasks(date: string): Task[] | null {
    return getTasksFromStorage(TASK_KEY(date));
  },

  saveTask(task: Task) {
    const currentInstances = getTasksFromStorage(TASK_KEY(task.date)) || [];

    const index = currentInstances.findIndex(
      (item) => item.id === task.id
    );
    if (index !== -1) {
      currentInstances[index] = task;
    } else {
      currentInstances.push(task);
    }

    saveToStorage(TASK_KEY(task.date), currentInstances);
  },
};
