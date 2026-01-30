import {
  ParentProps,
  createContext,
  createResource,
  useContext,
} from "solid-js";
import type { Alarm, Day, Event, Reminder, Routine, Task } from "@/types/api";
import { tomorrowAPI } from "@/utils/api";

export type TomorrowData = {
  day: () => Day | undefined;
  isDayLoading: () => boolean;
  dayError: () => unknown;

  events: () => Event[];
  isEventsLoading: () => boolean;
  eventsError: () => unknown;

  tasks: () => Task[];
  isTasksLoading: () => boolean;
  tasksError: () => unknown;

  routines: () => Routine[];
  isRoutinesLoading: () => boolean;
  routinesError: () => unknown;

  reminders: () => Reminder[];
  alarms: () => Alarm[];

  refetchAll: () => void;
};

const TomorrowDataContext = createContext<TomorrowData>();

export function TomorrowDataProvider(props: ParentProps) {
  const data = createTomorrowData();
  return (
    <TomorrowDataContext.Provider value={data}>
      {props.children}
    </TomorrowDataContext.Provider>
  );
}

export function useTomorrowData(): TomorrowData {
  const value = useContext(TomorrowDataContext);
  if (!value) {
    throw new Error("useTomorrowData must be used within TomorrowDataProvider");
  }
  return value;
}

function createTomorrowData(): TomorrowData {
  // Phase 1: ensure scheduled + get day shell (reminders/alarms live on Day)
  const [day, { refetch: refetchDay }] = createResource<Day>(() =>
    tomorrowAPI.ensureScheduled(),
  );

  // Phase 2: load each section independently, but ONLY after scheduling is done.
  // Otherwise multiple parallel endpoints could race and schedule repeatedly.
  const [events, { refetch: refetchEvents }] = createResource(
    () => day()?.id ?? null,
    async () => tomorrowAPI.getCalendarEntries(),
  );
  const [tasks, { refetch: refetchTasks }] = createResource(
    () => day()?.id ?? null,
    async () => tomorrowAPI.getTasks(),
  );
  const [routines, { refetch: refetchRoutines }] = createResource(
    () => day()?.id ?? null,
    async () => tomorrowAPI.getRoutines(),
  );

  const reminders = () => day()?.reminders ?? [];
  const alarms = () => day()?.alarms ?? [];

  const refetchAll = () => {
    refetchDay();
    refetchEvents();
    refetchTasks();
    refetchRoutines();
  };

  return {
    day: () => day(),
    isDayLoading: () => day.loading,
    dayError: () => day.error,

    events: () => events() ?? [],
    isEventsLoading: () => events.loading,
    eventsError: () => events.error,

    tasks: () => tasks() ?? [],
    isTasksLoading: () => tasks.loading,
    tasksError: () => tasks.error,

    routines: () => routines() ?? [],
    isRoutinesLoading: () => routines.loading,
    routinesError: () => routines.error,

    reminders,
    alarms,

    refetchAll,
  };
}
