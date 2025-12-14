import { Component, createMemo, Show } from "solid-js";
import type { Accessor } from "solid-js";
import { Day, Task, Event } from "types/api";

import { Icon } from "../shared/icon";
import TaskList from "../tasks/list";
import { formatTimeString } from "../tasks/list";
import EventList from "../events/list";

const DayHeader: Component<{ day: Day }> = (props) => {
  const date = () => new Date(props.day.date + "T12:00:00");
  const dayName = () => date().toLocaleDateString("en-US", { weekday: "long" });
  const monthDay = () =>
    date().toLocaleDateString("en-US", { month: "short", day: "numeric" });

  return (
    <header class="px-5 py-5 border-b border-gray-200">
      <div class="flex items-baseline justify-between">
        <div>
          <h1 class="text-2xl font-light tracking-tight text-gray-900">
            {dayName()}
          </h1>
          <p class="text-sm text-gray-400 mt-0.5">{monthDay()}</p>
        </div>
        <Show when={props.day.template_id}>
          <span class="text-xs uppercase tracking-wider text-gray-400">
            {props.day.template_id}
          </span>
        </Show>
      </div>

      <Show when={props.day.alarm}>
        <div class="mt-3 flex items-center gap-2 text-gray-500">
          <Icon key="clock" />
          <span class="text-xs">{formatTimeString(props.day.alarm!.time)}</span>
          <span class="text-xs text-gray-400 lowercase">
            · {props.day.alarm!.type.toLowerCase()}
          </span>
        </div>
      </Show>
    </header>
  );
};

const EmptyState: Component = () => (
  <div class="px-5 py-16 text-center">
    <p class="text-sm text-gray-400">Nothing scheduled</p>
  </div>
);

// ============================================
// Main Component
// ============================================

const SectionHeader: Component<{ label: string }> = (props) => (
  <div class="px-5 py-2 bg-gray-50 border-b border-gray-200">
    <span class="text-xs uppercase tracking-wider text-gray-400">
      {props.label}
    </span>
  </div>
);

interface DayViewProps {
  day: Accessor<Day>;
  events: Accessor<Event[]>;
  tasks: Accessor<Task[]>;
}

const DayView: Component<DayViewProps> = (props) => {
  const hasContent = () =>
    (props.events()?.length ?? 0) > 0 || (props.tasks()?.length ?? 0) > 0;

  const tasks = createMemo(() => {
    if (!props.tasks()) {
      return [];
    }
    console.log(props.events());

    return props.tasks().filter((t) => t.status === "READY");
  });

  return (
    <div class="min-h-screen bg-white">
      <DayHeader day={props.day()} />

      <Show when={hasContent()} fallback={<EmptyState />}>
        <main>
          <Show when={props.events()?.length}>
            <SectionHeader label="Events" />
            <EventList events={props.events} />
          </Show>

          <Show when={props.tasks()?.length}>
            <SectionHeader label="Tasks" />
            <TaskList tasks={tasks} />
          </Show>
        </main>
      </Show>

      {/* Bottom padding */}
      <div class="h-6" />
    </div>
  );
};

export default DayView;
