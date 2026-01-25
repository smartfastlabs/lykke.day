import {
  Component,
  Show,
  createMemo,
  createSignal,
  onCleanup,
  onMount,
} from "solid-js";
import Page from "@/components/shared/layout/Page";
import { useStreamingData } from "@/providers/streamingData";
import TimeBlocksSummary from "@/components/today/TimeBlocksSummary";
import {
  RightNowSection,
  UpcomingSection,
  RemindersSummary,
  EventsSection,
  TasksSection,
  RoutineSummary,
} from "@/components/today";
import { getTime } from "@/utils/dates";
import type { Event, Task } from "@/types/api";

const getTaskTime = (task: Task): Date | null => {
  const taskDate = task.scheduled_date;
  if (!taskDate || !task.schedule) return null;

  const schedule = task.schedule;

  if (schedule.timing_type === "FIXED_TIME" && schedule.start_time) {
    return getTime(taskDate, schedule.start_time);
  }

  if (schedule.timing_type === "DEADLINE" && schedule.end_time) {
    return getTime(taskDate, schedule.end_time);
  }

  if (schedule.available_time) {
    return getTime(taskDate, schedule.available_time);
  }

  if (schedule.start_time) {
    return getTime(taskDate, schedule.start_time);
  }

  return null;
};

const isAllDayEvent = (event: Event): boolean => {
  const start = new Date(event.starts_at);
  const end = event.ends_at ? new Date(event.ends_at) : null;
  if (!end) return false;
  const diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
  return diffHours >= 23;
};

const KioskPage: Component = () => {
  const { dayContext, isLoading, day, tasks, events, reminders, routines } =
    useStreamingData();
  const [now, setNow] = createSignal(new Date());

  onMount(() => {
    const interval = setInterval(() => {
      setNow(new Date());
    }, 30000);

    onCleanup(() => {
      clearInterval(interval);
    });
  });

  const date = createMemo(() => {
    const dayValue = day();
    if (!dayValue) return new Date();

    const [year, month, dayNum] = dayValue.date.split("-").map(Number);
    return new Date(year, month - 1, dayNum);
  });

  const weekday = createMemo(() =>
    new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(date())
  );

  const monthDay = createMemo(() =>
    new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
    }).format(date())
  );

  const dateLabel = createMemo(() => `${weekday()} ${monthDay()}`);
  const planTitle = createMemo(() => day()?.high_level_plan?.title?.trim() ?? "");
  const isWorkday = createMemo(() => Boolean(day()?.tags?.includes("WORKDAY")));
  const timeBlocks = createMemo(() => day()?.template?.time_blocks ?? []);
  const dayDate = createMemo(() => day()?.date);

  const allTasks = createMemo(() => tasks() ?? []);
  const allEvents = createMemo(() => events() ?? []);
  const allReminders = createMemo(() => reminders() ?? []);
  const allRoutines = createMemo(() => routines() ?? []);

  const rightNowEventIds = createMemo(() => {
    const currentTime = now();
    return new Set(
      allEvents()
        .filter((event) => {
          if (isAllDayEvent(event)) return false;
          const start = new Date(event.starts_at);
          const end = event.ends_at ? new Date(event.ends_at) : null;
          return start <= currentTime && (!end || end >= currentTime);
        })
        .map((event) => event.id)
        .filter((id): id is string => Boolean(id))
    );
  });

  const upcomingEventIds = createMemo(() => {
    const currentTime = now();
    const windowEnd = new Date(currentTime.getTime() + 1000 * 30 * 60);
    return new Set(
      allEvents()
        .filter((event) => {
          if (isAllDayEvent(event)) return false;
          const start = new Date(event.starts_at);
          const end = event.ends_at ? new Date(event.ends_at) : null;
          if (start <= currentTime && (!end || end >= currentTime)) {
            return false;
          }
          return start >= currentTime && start <= windowEnd;
        })
        .map((event) => event.id)
        .filter((id): id is string => Boolean(id))
    );
  });

  const rightNowTaskIds = createMemo(() => {
    const currentTime = now();
    return new Set(
      allTasks()
        .filter((task) => {
          if (task.status === "COMPLETE" || task.status === "PUNT") {
            return false;
          }
          const taskTime = getTaskTime(task);
          if (!taskTime) return false;
          return taskTime < currentTime;
        })
        .map((task) => task.id)
        .filter((id): id is string => Boolean(id))
    );
  });

  const upcomingTaskIds = createMemo(() => {
    const currentTime = now();
    const windowEnd = new Date(currentTime.getTime() + 1000 * 30 * 60);
    return new Set(
      allTasks()
        .filter((task) => {
          if (task.status === "COMPLETE" || task.status === "PUNT") {
            return false;
          }
          const taskTime = getTaskTime(task);
          if (!taskTime) return false;
          if (taskTime < currentTime) return false;
          return taskTime <= windowEnd;
        })
        .map((task) => task.id)
        .filter((id): id is string => Boolean(id))
    );
  });

  const eventsForSections = createMemo(() => {
    const ids = new Set<string>();
    rightNowEventIds().forEach((id) => ids.add(id));
    upcomingEventIds().forEach((id) => ids.add(id));
    return allEvents().filter((event) => {
      const eventId = event.id;
      if (!eventId) return true;
      return !ids.has(eventId);
    });
  });

  const tasksForSections = createMemo(() => {
    const ids = new Set<string>();
    rightNowTaskIds().forEach((id) => ids.add(id));
    upcomingTaskIds().forEach((id) => ids.add(id));
    return allTasks().filter((task) => {
      const taskId = task.id;
      if (!taskId) return true;
      return !ids.has(taskId);
    });
  });

  const hasUpcomingEvents = createMemo(() =>
    allEvents().some((event) => new Date(event.starts_at) >= new Date())
  );

  return (
    <Page variant="app" hideFooter hideFloatingButtons>
      <div class="min-h-[100dvh] h-[100dvh] box-border relative overflow-hidden">
        <Show
          when={!isLoading() && dayContext()}
          fallback={
            <div class="relative z-10 p-8 text-center text-stone-400">
              Loading...
            </div>
          }
        >
          <div class="relative z-10 h-full max-w-[1024px] mx-auto px-5 py-4 flex flex-col gap-3">
            <div class="flex items-start justify-between gap-4">
              <div>
                <div class="flex items-center gap-3 text-stone-600">
                  <span class="font-semibold text-lg text-amber-600/80">
                    {planTitle() || dateLabel()}
                  </span>
                </div>
                <Show when={planTitle()}>
                  <p class="text-[11px] uppercase tracking-[0.2em] text-amber-600/80">
                    {dateLabel()}
                  </p>
                </Show>
              </div>
              <Show when={isWorkday()}>
                <span class="px-3 py-1 rounded-full bg-amber-50/95 text-amber-600 text-[11px] font-semibold uppercase tracking-wide border border-amber-100/80 shadow-sm shadow-amber-900/5">
                  Workday
                </span>
              </Show>
            </div>
            <TimeBlocksSummary timeBlocks={timeBlocks()} dayDate={dayDate()} />
            <div class="flex-1 grid grid-cols-2 gap-4 overflow-hidden">
              <div class="flex flex-col gap-3 overflow-hidden">
                <div class="shrink-0">
                  <RightNowSection events={allEvents()} tasks={allTasks()} />
                </div>
                <div class="shrink-0">
                  <UpcomingSection events={allEvents()} tasks={allTasks()} />
                </div>
                <div class="shrink-0">
                  <RemindersSummary
                    reminders={allReminders()}
                    href="/me/today/reminders"
                  />
                </div>
              </div>
              <div class="flex flex-col gap-3 overflow-hidden">
                <Show when={hasUpcomingEvents()}>
                  <div class="shrink-0">
                    <EventsSection
                      events={eventsForSections()}
                      href="/me/today/events"
                    />
                  </div>
                </Show>
                <div class="shrink-0">
                  <TasksSection tasks={tasksForSections()} href="/me/today/tasks" />
                </div>
                <div class="shrink-0">
                  <RoutineSummary tasks={allTasks()} routines={allRoutines()} />
                </div>
              </div>
            </div>
          </div>
        </Show>
      </div>
    </Page>
  );
};

export default KioskPage;
