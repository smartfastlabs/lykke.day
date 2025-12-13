import {
  createSignal,
  createContext,
  createResource,
  useContext,
  onMount,
} from "solid-js";
import { DayContext } from "../types/api";
import { dayAPI } from "../utils/api";

const SheppardContext = createContext();

export function SheppardProvider(props) {
  const [tasks, taskManager] = createResource<Task[]>(() => []);
  const [events, eventManager] = createResource<Event[]>(() => []);
  const [day, dayManager] = createResource<Day | null>(() => null);
  const [dayContext, dayContextManager] = createResource<DayContext | null>(
    () => null
  );

  onMount(async () => {
    const ctx = await dayAPI.getToday();
    taskManager.mutate(ctx.tasks);
    eventManager.mutate(ctx.event);
  });

  const updateTask = async (input: Any) => {
    taskManager.mutate((items) =>
      items.map((i) => (i.id !== input.id ? i : { ...i, ...input }))
    );
    return input;
  };

  const setTaskStatus = async (task: Any, status: Any) => {
    await updateTask(await TaskService.setTaskStatus(task, status));
  };

  const value = {
    tasks,
    events,
    updateTask,
    setTaskStatus,
  };

  return (
    <SheppardContext.Provider value={value}>
      {props.children}
    </SheppardContext.Provider>
  );
}

export function useSheppardManager() {
  const context = useContext(SheppardContext);
  if (!context) {
    throw new Error(
      "useSheppardManager must be used within a SheppardProvider"
    );
  }
  return context;
}
