import { Component, Show, createMemo } from "solid-js";
import { useStreamingData } from "@/providers/streamingData";
import {
  TasksSection,
  EventsSection,
  RoutinesSummary,
  RemindersSummary,
  UpcomingSection,
  RightNowSection,
} from "@/components/today";

export const TodayPage: Component = () => {
  const { tasks, events, reminders } = useStreamingData();

  const allTasks = createMemo(() => tasks() ?? []);
  const allEvents = createMemo(() => events() ?? []);
  const allReminders = createMemo(() => reminders() ?? []);
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
        <RemindersSummary reminders={allReminders()} />
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
