import { Component, createMemo } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import { TasksSection, EventsSection } from "@/components/today";
import { Hero } from "@/components/today";

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) {
    return "Good morning.";
  } else if (hour < 17) {
    return "Good afternoon.";
  } else {
    return "Good evening.";
  }
}

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

  return (
    <>
      <Hero
        weekday={weekday()}
        monthDay={monthDay()}
        isWorkday={isWorkday()}
        greeting={getGreeting()}
        description="A balanced day ahead with a mix of focus work and personal tasks. You have a few meetings scheduled, but plenty of time for deep work in the morning. The afternoon looks lighter, perfect for catching up on tasks and taking a break."
      />
      <div class="grid md:grid-cols-2 gap-4 md:gap-6">
        <TasksSection tasks={allTasks()} href="/me/today/tasks" />
        <EventsSection events={allEvents()} href="/me/today/events" />
      </div>
    </>
  );
};

export default TodayPage;
