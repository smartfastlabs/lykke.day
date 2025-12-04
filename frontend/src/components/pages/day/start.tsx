import Page from "../../shared/layout/page";
import { getTime } from "../../../utils/dates";
import TimeBadge from "../../shared/timeBadge";
import { createMemo, For, Component, createResource } from "solid-js";
import { home } from "solid-heroicons/outline";
import TaskCard from "../../tasks/card";
import { eventAPI, planningAPI } from "../../../utils/api";

function EventRow(event) {
  const startTime = createMemo(() => {
    if (event.starts_at) {
      return getTime(event.date, event.starts_at);
    }
  });

  return (
    <div class="group flex items-center justify-between gap-4 px-4 py-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors">
      <div class="flex flex-col min-w-0">
        <h3 class="text-gray-900 font-medium truncate">{event.name}</h3>
        <span class="text-xs text-gray-400 tracking-wide uppercase">
          {event.platform}
        </span>
      </div>
      <Show when={startTime()}>
        <TimeBadge value={startTime()} />
      </Show>
    </div>
  );
}

function TaskRow(task) {
  const startTime = createMemo(() => {
    const v = task.schedule.start_time || task.schedule.end_time;
    if (v) {
      return getTime(task.date, v);
    }
  });

  return (
    <div class="group flex items-center justify-between gap-4 px-4 py-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors">
      <div class="flex flex-col min-w-0">
        <h3 class="text-gray-900 font-medium truncate">{task.name}</h3>
        <span class="text-xs text-gray-400 tracking-wide uppercase">
          {task.task_definition.type}
        </span>
      </div>
      <Show when={startTime()}>
        <TimeBadge value={startTime()} />
      </Show>
    </div>
  );
}

export const DayStart: Component = () => {
  const [tasks] = createResource<Any[]>(planningAPI.previewToday);
  const [events] = createResource<Any[]>(eventAPI.getTodays);
  return (
    <Page>
      <For each={tasks()}>{(task) => <TaskRow {...task} />}</For>
      <For each={events()}>{(event) => <EventRow {...event} />}</For>
    </Page>
  );
};

export default DayStart;
