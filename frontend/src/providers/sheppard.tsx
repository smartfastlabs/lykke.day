import {
  createSignal,
  createContext,
  createResource,
  useContext,
  onMount,
  type Resource,
  type Component,
  type ParentProps,
} from "solid-js";
import { DayContext, Task, Event, Day } from "../types/api";
import { dayAPI, taskAPI } from "../utils/api";
import type { TaskStatus } from "../types/api";

interface SheppardContextValue {
  tasks: Resource<Task[]>;
  events: Resource<Event[]>;
  day: Resource<Day | null>;
  dayContext: Resource<DayContext | null>;
  updateTask: (input: Task) => Promise<Task>;
  setTaskStatus: (task: Task, status: TaskStatus) => Promise<void>;
}

const SheppardContext = createContext<SheppardContextValue>();

export function SheppardProvider(props: ParentProps) {
  const [tasks, taskManager] = createResource<Task[]>(() => []);
  const [events, eventManager] = createResource<Event[]>(() => []);
  const [day, dayManager] = createResource<Day | null>(() => null);
  const [dayContext, dayContextManager] = createResource<DayContext | null>(
    () => null
  );

  onMount(async () => {
    const ctx = await dayAPI.getToday();
    dayContextManager.mutate(ctx);
    dayManager.mutate(ctx.day);
    taskManager.mutate(ctx.tasks || []);
    eventManager.mutate(ctx.events || []);
  });

  const updateTask = async (input: Task): Promise<Task> => {
    taskManager.mutate((items) =>
      items.map((i) => (i.id !== input.id ? i : { ...i, ...input }))
    );
    return input;
  };

  const setTaskStatus = async (task: Task, status: TaskStatus): Promise<void> => {
    const updatedTask = await taskAPI.setTaskStatus(task, status);
    await updateTask(updatedTask);
  };

  const value: SheppardContextValue = {
    tasks,
    events,
    day,
    dayContext,
    updateTask,
    setTaskStatus,
  };

  return (
    <SheppardContext.Provider value={value}>
      {props.children}
    </SheppardContext.Provider>
  );
}

export function useSheppardManager(): SheppardContextValue {
  const context = useContext(SheppardContext);
  if (!context) {
    throw new Error(
      "useSheppardManager must be used within a SheppardProvider"
    );
  }
  return context;
}
