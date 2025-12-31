import {
  createContext,
  createResource,
  createMemo,
  useContext,
  type Accessor,
  type ParentProps,
  type ResourceReturn,
} from "solid-js";
import { DayContext, Task, Event, Day, TaskStatus } from "../types/api";
import { dayAPI, taskAPI } from "../utils/api";

interface SheppardContextValue {
  // The main resource - provides loading/error states
  dayContextResource: ResourceReturn<DayContext>;
  // Derived accessors for convenience
  dayContext: Accessor<DayContext | undefined>;
  tasks: Accessor<Task[]>;
  events: Accessor<Event[]>;
  day: Accessor<Day | undefined>;
  // Loading and error states
  isLoading: Accessor<boolean>;
  error: Accessor<Error | undefined>;
  // Actions
  refetch: () => void;
  setTaskStatus: (task: Task, status: TaskStatus) => Promise<void>;
}

const SheppardContext = createContext<SheppardContextValue>();

export function SheppardProvider(props: ParentProps) {
  // Single resource that fetches all day context data
  const [dayContext, { refetch, mutate }] = createResource(dayAPI.getToday);

  // Derived values from the resource
  const tasks = createMemo(() => dayContext()?.tasks ?? []);
  const events = createMemo(() => dayContext()?.events ?? []);
  const day = createMemo(() => dayContext()?.day);
  const isLoading = createMemo(() => dayContext.loading);
  const error = createMemo(() => dayContext.error);

  // Optimistically update a task in the local state
  const updateTaskLocally = (updatedTask: Task) => {
    mutate((current) => {
      if (!current) return current;
      return {
        ...current,
        tasks: current.tasks?.map((t) =>
          t.id === updatedTask.id ? updatedTask : t
        ),
      };
    });
  };

  const setTaskStatus = async (task: Task, status: TaskStatus): Promise<void> => {
    // Optimistic update
    const previousTask = task;
    updateTaskLocally({ ...task, status });

    try {
      const updatedTask = await taskAPI.setTaskStatus(task, status);
      updateTaskLocally(updatedTask);
    } catch (error) {
      // Rollback on error
      updateTaskLocally(previousTask);
      throw error;
    }
  };

  const value: SheppardContextValue = {
    dayContextResource: [dayContext, { refetch, mutate }],
    dayContext: () => dayContext(),
    tasks,
    events,
    day,
    isLoading,
    error,
    refetch,
    setTaskStatus,
  };

  return (
    <SheppardContext.Provider value={value}>
      {props.children}
    </SheppardContext.Provider>
  );
}

export function useSheppard(): SheppardContextValue {
  const context = useContext(SheppardContext);
  if (!context) {
    throw new Error("useSheppard must be used within a SheppardProvider");
  }
  return context;
}

// Backwards compatibility alias - can be removed later
export const useSheppardManager = useSheppard;
