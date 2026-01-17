import { Component, createMemo } from "solid-js";
import { useStreamingData } from "@/providers/streaming-data";
import {
  TasksSection,
  EventsSection,
  RoutinesSummary,
  GoalsSummary,
  UpcomingSection,
  RightNowSection,
  TimeBlocksSummary,
} from "@/components/today";

export const TodayPage: Component = () => {
  const { tasks, events, goals, day } = useStreamingData();

  const allTasks = createMemo(() => tasks() ?? []);
  const allEvents = createMemo(() => events() ?? []);
  const allGoals = createMemo(() => goals() ?? []);
  const timeBlocks = createMemo(() => day()?.template?.time_blocks ?? []);
  const dayDate = createMemo(() => day()?.date);

  return (
    <>
      <div class="mb-6">
        <RightNowSection events={allEvents()} tasks={allTasks()} />
      </div>
      <div class="mb-6">
        <TimeBlocksSummary timeBlocks={timeBlocks()} dayDate={dayDate()} />
      </div>
      <div class="mb-6">
        <UpcomingSection events={allEvents()} tasks={allTasks()} />
      </div>
      <div class="mb-6">
        <GoalsSummary goals={allGoals()} />
      </div>

      <div class="mb-6">
        <RoutinesSummary tasks={allTasks()} />
      </div>

      <div class="mb-6">
        <EventsSection events={allEvents()} href="/me/today/events" />
      </div>

      <div class="mb-6">
        <TasksSection tasks={allTasks()} href="/me/today/tasks" />
      </div>
    </>
  );
};

export default TodayPage;
