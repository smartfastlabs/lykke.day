import {
  Component,
  Show,
  createMemo,
  createEffect,
  createSignal,
  onMount,
  onCleanup,
} from "solid-js";
import { useNavigate, useLocation } from "@solidjs/router";
import { useStreamingData } from "@/providers/streamingData";
import {
  TasksSection,
  EventsSection,
  RoutineSummary,
  RemindersSummary,
  AlarmsSummary,
  UpcomingSection,
  RightNowSection,
} from "@/components/today";
import { getShowTodayCookie } from "@/utils/cookies";
import { filterVisibleTasks } from "@/utils/tasks";
import type { Event } from "@/types/api";

const isAllDayEvent = (event: Event): boolean => {
  const start = new Date(event.starts_at);
  const end = event.ends_at ? new Date(event.ends_at) : null;
  if (!end) return false;
  const diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
  return diffHours >= 23;
};

export const TodayPage: Component = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { tasks, events, reminders, alarms, routines } = useStreamingData();
  const [now, setNow] = createSignal(new Date());

  // Update time every 30 seconds to keep sections aligned
  onMount(() => {
    const interval = setInterval(() => {
      setNow(new Date());
    }, 30000);

    onCleanup(() => {
      clearInterval(interval);
    });
  });

  const allTasks = createMemo(() => tasks() ?? []);
  const allEvents = createMemo(() => events() ?? []);
  const allReminders = createMemo(() => reminders() ?? []);
  const allAlarms = createMemo(() => alarms() ?? []);
  const allRoutines = createMemo(() => routines() ?? []);

  // Check if all reminders are complete or punted
  const allRemindersDone = createMemo(() => {
    const remindersList = allReminders();
    if (remindersList.length === 0) return true; // No reminders means "done"
    return remindersList.every(
      (r) => r.status === "COMPLETE" || r.status === "PUNT",
    );
  });

  // Check if all tasks are complete or punted
  const allTasksDone = createMemo(() => {
    const tasksList = allTasks();
    if (tasksList.length === 0) return true; // No tasks means "done"
    return tasksList.every(
      (t) => t.status === "COMPLETE" || t.status === "PUNT",
    );
  });

  // Check if there are no more events (no upcoming or ongoing events)
  const noMoreEvents = createMemo(() => {
    const now = new Date();
    return !allEvents().some((event) => {
      const start = new Date(event.starts_at);
      const end = event.ends_at ? new Date(event.ends_at) : null;
      // Check if event is upcoming (hasn't started) or ongoing (started but not ended)
      return start >= now || (start <= now && (!end || end >= now));
    });
  });

  // Check if it's end of day
  const isEndOfDay = createMemo(
    () => allRemindersDone() && allTasksDone() && noMoreEvents(),
  );

  // Redirect to /me/thats-all-for-today if it's end of day, unless user
  // chose "Back to home" from thats-all (short-lived cookie set).
  createEffect(() => {
    if (!isEndOfDay() || location.pathname === "/me/thats-all-for-today")
      return;
    if (getShowTodayCookie()) {
      return; // stay on /me, show today view
    }
    navigate("/me/thats-all-for-today", { replace: true });
  });

  const hasUpcomingEvents = createMemo(() =>
    allEvents().some((event) => new Date(event.starts_at) >= new Date()),
  );

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
        .filter((id): id is string => Boolean(id)),
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
        .filter((id): id is string => Boolean(id)),
    );
  });

  const rightNowTaskIds = createMemo(() => {
    return new Set(
      allTasks()
        .filter((task) => task.timing_status === "past-due")
        .map((task) => task.id)
        .filter((id): id is string => Boolean(id)),
    );
  });

  const upcomingTaskIds = createMemo(() => {
    return new Set(
      allTasks()
        .filter((task) => task.timing_status === "inactive")
        .map((task) => task.id)
        .filter((id): id is string => Boolean(id)),
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
    return filterVisibleTasks(allTasks()).filter((task) => {
      const taskId = task.id;
      if (!taskId) return true;
      if (ids.has(taskId)) return false;
      return true;
    });
  });

  return (
    <>
      <div class="mb-3">
        <RightNowSection events={allEvents()} tasks={allTasks()} />
      </div>
      <div class="mb-3">
        <UpcomingSection events={allEvents()} tasks={allTasks()} />
      </div>
      <div class="mb-6">
        <RemindersSummary
          reminders={allReminders()}
          href="/me/today/reminders"
        />
      </div>
      <div class="mb-6">
        <AlarmsSummary alarms={allAlarms()} href="/me/today/alarms" />
      </div>
      <div class="mb-6 flex flex-col md:flex-row gap-4">
        <Show when={hasUpcomingEvents()}>
          <div class="w-full md:w-1/2">
            <EventsSection
              events={eventsForSections()}
              href="/me/today/events"
            />
          </div>
        </Show>
        <div class={hasUpcomingEvents() ? "w-full md:w-1/2" : "w-full"}>
          <TasksSection tasks={tasksForSections()} href="/me/today/tasks" />
        </div>
      </div>

      <div class="mb-6">
        <RoutineSummary tasks={allTasks()} routines={allRoutines()} />
      </div>
    </>
  );
};

export default TodayPage;
