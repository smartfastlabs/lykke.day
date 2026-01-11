import { Component, createMemo } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import { TasksSection, EventsSection } from "@/components/overview";

export const PreviewView: Component = () => {
  const { tasks, events } = useSheppard();

  const allTasks = createMemo(() => tasks() ?? []);
  const allEvents = createMemo(() => events() ?? []);

  return (
    <div class="grid md:grid-cols-2 gap-4 md:gap-6">
      <TasksSection tasks={allTasks()} href="/me/today/tasks" />
      <EventsSection events={allEvents()} href="/me/today/events" />
    </div>
  );
};

export default PreviewView;
