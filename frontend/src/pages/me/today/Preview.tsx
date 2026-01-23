import { Component, createMemo } from "solid-js";
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
        <div class="w-full md:w-1/2">
          <EventsSection events={allEvents()} href="/me/today/events" />
        </div>
        <div class="w-full md:w-1/2">
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
