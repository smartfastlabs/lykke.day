import { Component, createMemo } from "solid-js";
import { useStreamingData } from "@/providers/streaming-data";
import {
  TasksSection,
  EventsSection,
  RoutinesSummary,
  GoalsSummary,
} from "@/components/today";
import { Hero } from "@/components/today";

export const TodayPage: Component = () => {
  const { tasks, events, goals, day } = useStreamingData();

  const allTasks = createMemo(() => tasks() ?? []);
  const allEvents = createMemo(() => events() ?? []);
  const allGoals = createMemo(() => goals() ?? []);

  const date = createMemo(() => {
    const dayValue = day();
    return dayValue ? new Date(dayValue.date) : new Date();
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

  const isWorkday = createMemo(() => {
    const dayValue = day();
    return Boolean(dayValue?.tags?.includes("WORKDAY"));
  });

  const assistantMessage = createMemo(() => {
    const taskCount = allTasks().length;
    const eventCount = allEvents().length;

    if (taskCount === 0 && eventCount === 0) {
      return "You have a clear schedule today. This is a great opportunity to tackle something meaningful or simply take time to rest.";
    }

    if (isWorkday()) {
      return `I've prepared your day with ${taskCount} task${taskCount !== 1 ? "s" : ""} and ${eventCount} event${eventCount !== 1 ? "s" : ""}. You have good blocks of focus time scheduled. I suggest starting with your most important task while your energy is fresh.`;
    }

    return `Here's what's on your plate: ${taskCount} task${taskCount !== 1 ? "s" : ""} and ${eventCount} event${eventCount !== 1 ? "s" : ""}. Take it at your own pace and remember to take breaks when you need them.`;
  });

  return (
    <>
      <Hero
        weekday={weekday()}
        monthDay={monthDay()}
        isWorkday={isWorkday()}
        greeting={`Your ${weekday()} overview`}
        description={assistantMessage()}
      />

      <div class="mb-6">
        <RoutinesSummary tasks={allTasks()} />
      </div>

<<<<<<< Updated upstream
      <div class="mb-6">
        <GoalsSummary goals={allGoals()} />
      </div>

      <div class="mb-6">
=======
      <div class="space-y-4 md:space-y-6 mb-6">
>>>>>>> Stashed changes
        <EventsSection events={allEvents()} href="/me/today/events" />
      </div>

      <div class="mb-6">
        <TasksSection tasks={allTasks()} href="/me/today/tasks" />
      </div>
    </>
  );
};

export default TodayPage;
