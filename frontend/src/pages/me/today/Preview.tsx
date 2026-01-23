import { Component, Show, createMemo, createEffect } from "solid-js";
import { useNavigate, useLocation } from "@solidjs/router";
import { useStreamingData } from "@/providers/streamingData";
import {
  TasksSection,
  EventsSection,
  RoutinesSummary,
  RemindersSummary,
  UpcomingSection,
  RightNowSection,
} from "@/components/today";
import { getShowTodayCookie } from "@/utils/cookies";

export const TodayPage: Component = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { tasks, events, reminders } = useStreamingData();

  const allTasks = createMemo(() => tasks() ?? []);
  const allEvents = createMemo(() => events() ?? []);
  const allReminders = createMemo(() => reminders() ?? []);

  // Check if all reminders are complete or punted
  const allRemindersDone = createMemo(() => {
    const remindersList = allReminders();
    if (remindersList.length === 0) return true; // No reminders means "done"
    return remindersList.every(
      (r) => r.status === "COMPLETE" || r.status === "PUNT"
    );
  });

  // Check if all tasks are complete or punted
  const allTasksDone = createMemo(() => {
    const tasksList = allTasks();
    if (tasksList.length === 0) return true; // No tasks means "done"
    return tasksList.every(
      (t) => t.status === "COMPLETE" || t.status === "PUNT"
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
    () => allRemindersDone() && allTasksDone() && noMoreEvents()
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
    allEvents().some((event) => new Date(event.starts_at) >= new Date())
  );

  return (
    <>
      <div class="mb-3">
        <RightNowSection events={allEvents()} tasks={allTasks()} />
      </div>
      <div class="mb-3">
        <UpcomingSection events={allEvents()} tasks={allTasks()} />
      </div>
      <div class="mb-6">
        <RemindersSummary reminders={allReminders()} href="/me/today/reminders" />
      </div>

      <div class="mb-6 flex flex-col md:flex-row gap-4">
        <Show when={hasUpcomingEvents()}>
          <div class="w-full md:w-1/2">
            <EventsSection events={allEvents()} href="/me/today/events" />
          </div>
        </Show>
        <div class={hasUpcomingEvents() ? "w-full md:w-1/2" : "w-full"}>
          <TasksSection tasks={allTasks()} href="/me/today/tasks" />
        </div>
      </div>

      <div class="mb-6">
        <RoutinesSummary tasks={allTasks()} />
      </div>
    </>
  );
};

export default TodayPage;
