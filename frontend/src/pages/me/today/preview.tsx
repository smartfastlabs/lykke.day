import { Component, createMemo } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import {
  TasksSection,
  EventsSection,
  RoutinesSummary,
} from "@/components/today";
import { Hero } from "@/components/today";

export const TodayPage: Component = () => {
  const { tasks, events, day } = useSheppard();

  const allTasks = createMemo(() => tasks() ?? []);
  const allEvents = createMemo(() => events() ?? []);

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

      <div class="grid md:grid-cols-2 gap-4 md:gap-6 mb-6">
        <EventsSection events={allEvents()} href="/me/today/events" />
        <TasksSection tasks={allTasks()} href="/me/today/tasks" />
      </div>
    </>
  );
};

export default TodayPage;
