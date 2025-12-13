import { Component, For, Show } from "solid-js";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { getCategoryIcon, getIcon, getTypeIcon } from "../../../utils/icons";
import {
  TaskStatus,
  DayContext,
  Day,
  Task,
  Event,
  TaskSchedule,
} from "types/api";

const formatTimeString = (timeStr: string): string => {
  const [h, m] = timeStr.split(":");
  const hour = parseInt(h);
  const ampm = hour >= 12 ? "p" : "a";
  const hour12 = hour % 12 || 12;
  return `${hour12}:${m}${ampm}`;
};

const formatDateTime = (dateTimeStr: string): string => {
  const date = new Date(dateTimeStr);
  return date
    .toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    .toLowerCase()
    .replace(" ", "");
};

const isAllDayEvent = (event: Event): boolean => {
  const start = new Date(event.starts_at);
  const end = event.ends_at ? new Date(event.ends_at) : null;
  if (!end) return false;
  const diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
  return diffHours >= 23;
};

interface TimeDisplay {
  primary: string | null;
  secondary: string | null;
}

const getTimeDisplay = (schedule?: TaskSchedule): TimeDisplay | null => {
  if (!schedule) return null;

  if (schedule.timing_type === "TIME_WINDOW" && schedule.start_time) {
    return {
      primary: formatTimeString(schedule.start_time),
      secondary: schedule.end_time ? formatTimeString(schedule.end_time) : null,
    };
  }

  if (schedule.timing_type === "FIXED_TIME" && schedule.start_time) {
    return {
      primary: formatTimeString(schedule.start_time),
      secondary: null,
    };
  }

  if (schedule.timing_type === "DEADLINE") {
    return {
      primary: schedule.end_time
        ? `by ${formatTimeString(schedule.end_time)}`
        : null,
      secondary: null,
    };
  }
  if (schedule.timing_type === "FLEXIBLE") {
    if (schedule.available_time) {
      return {
        primary: `after ${formatTimeString(schedule.available_time)}`,
        secondary: null,
      };
    }
    if (schedule.end_time) {
      return {
        primary: `before ${formatTimeString(schedule.end_time)}`,
        secondary: null,
      };
    }
  }

  return null;
};

const getStatusClasses = (status: TaskStatus): string => {
  switch (status) {
    case "COMPLETE":
      return "bg-gray-100";
    case "PUNTED":
      return "bg-gray-50 italic";
    case "NOT_READY":
      return "opacity-40";
    default:
      return "";
  }
};

// ============================================
// Icons
// ============================================

const FaIcon: Component<{ icon: IconDefinition; class?: string }> = (props) => (
  <svg
    viewBox={`0 0 ${props.icon.icon[0]} ${props.icon.icon[1]}`}
    class={props.class ?? "w-4 h-4 fill-gray-400"}
  >
    <path d={props.icon.icon[4] as string} />
  </svg>
);

// ============================================
// Sub-components
// ============================================

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
          <FaIcon icon={getIcon("clock")} />
          <span class="text-xs">{formatTimeString(props.day.alarm!.time)}</span>
          <span class="text-xs text-gray-400 lowercase">
            · {props.day.alarm!.type.toLowerCase()}
          </span>
        </div>
      </Show>
    </header>
  );
};

const AllDayEventItem: Component<{ event: Event }> = (props) => {
  const icon = () => getTypeIcon("EVENT");

  return (
    <div class="group px-5 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer">
      <div class="flex items-center gap-4">
        <div class="w-14 flex-shrink-0 text-right">
          <span class="text-xs text-gray-400">all day</span>
        </div>
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <span class="w-4 flex-shrink-0 flex items-center justify-center">
            <Show when={icon()}>
              <FaIcon icon={icon()!} />
            </Show>
          </span>
          <span class="text-sm text-gray-700 truncate">{props.event.name}</span>
        </div>
      </div>
    </div>
  );
};

const TimedEventItem: Component<{ event: Event }> = (props) => {
  const icon = () => getTypeIcon("EVENT");

  return (
    <div class="group px-5 py-3.5 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer">
      <div class="flex items-center gap-4">
        <div class="w-14 flex-shrink-0 text-right">
          <span class="text-xs tabular-nums text-gray-500">
            {formatDateTime(props.event.starts_at)}
          </span>
        </div>
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <span class="w-4 flex-shrink-0 flex items-center justify-center">
            <Show when={icon()}>
              <FaIcon icon={icon()!} />
            </Show>
          </span>
          <span class="text-sm font-medium text-gray-800 truncate">
            {props.event.name}
          </span>
        </div>
        <Show when={props.event.people?.length}>
          <span class="text-xs text-gray-400 truncate max-w-24">
            {props.event.people!.map((p) => p.name).join(", ")}
          </span>
        </Show>
      </div>
    </div>
  );
};

const TaskItem: Component<{ task: Task }> = (props) => {
  const time = () => getTimeDisplay(props.task.schedule);
  const icon = () =>
    getCategoryIcon(props.task.category) ||
    getTypeIcon(props.task.task_definition?.type);

  return (
    <div
      class={`group px-5 py-3.5 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer ${getStatusClasses(
        props.task.status
      )}`}
    >
      <div class="flex items-center gap-4">
        {/* Time column */}
        <div class="w-14 flex-shrink-0 text-right">
          <Show
            when={time()?.primary}
            fallback={<span class="text-xs text-gray-300">—</span>}
          >
            <span
              class={`text-xs tabular-nums ${
                time()?.primary === "flexible"
                  ? "text-gray-400 italic"
                  : "text-gray-500"
              }`}
            >
              {time()?.primary}
            </span>
          </Show>
        </div>

        {/* Category/Type icon */}
        <span class="w-4 flex-shrink-0 flex items-center justify-center">
          <Show when={icon()}>
            <FaIcon icon={icon()!} />
          </Show>
        </span>

        {/* Task name */}
        <div class="flex-1 min-w-0">
          <span
            class={`text-sm truncate block ${
              props.task.status === "COMPLETE"
                ? "line-through text-gray-400"
                : "text-gray-800"
            }`}
          >
            {props.task.name.replace("Routine: ", "")}
          </span>
        </div>

        <Show when={props.task.status === "COMPLETE"}>
          <div class="flex-shrink-0 w-4">
            <FaIcon icon={getIcon("checkMark")} />
          </div>
        </Show>
      </div>
    </div>
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

// Sorting helpers
const parseTimeToMinutes = (timeStr?: string | null): number | null => {
  if (!timeStr) return null;
  const [h, m] = timeStr.split(":").map(Number);
  return h * 60 + m;
};

const getTaskSortTime = (task: Task): number => {
  const schedule = task.schedule;
  if (!schedule) return Infinity;

  // Use start_time for TIME_WINDOW and FIXED_TIME
  if (schedule.start_time) {
    return parseTimeToMinutes(schedule.start_time) ?? Infinity;
  }
  // Use end_time for DEADLINE
  if (schedule.end_time) {
    return parseTimeToMinutes(schedule.end_time) ?? Infinity;
  }
  // Use available_time as fallback
  if (schedule.available_time) {
    return parseTimeToMinutes(schedule.available_time) ?? Infinity;
  }
  return Infinity;
};

const sortTasks = (tasks: Task[]): Task[] => {
  return [...tasks].sort((a, b) => getTaskSortTime(a) - getTaskSortTime(b));
};

const sortEvents = (events: Event[]): Event[] => {
  return [...events].sort((a, b) => {
    const aTime = new Date(a.starts_at).getTime();
    const bTime = new Date(b.starts_at).getTime();
    return aTime - bTime;
  });
};

const DayView: Component<{ context: DayContext }> = (props) => {
  const hasContent = () =>
    (props.context.events?.length ?? 0) > 0 ||
    (props.context.tasks?.length ?? 0) > 0;

  const allDayEvents = () =>
    sortEvents(props.context.events?.filter(isAllDayEvent) ?? []);
  const timedEvents = () =>
    sortEvents(props.context.events?.filter((e) => !isAllDayEvent(e)) ?? []);

  const task = () => sortTasks(props.context.tasks ?? []);
  const flexibleTasks = () =>
    sortTasks(
      props.context.tasks?.filter(
        (t) => t.schedule?.timing_type === "FLEXIBLE"
      ) ?? []
    );

  return (
    <div class="min-h-screen bg-white">
      <DayHeader day={props.context.day} />

      <Show when={hasContent()} fallback={<EmptyState />}>
        <main>
          {/* Events section */}
          <Show when={allDayEvents().length > 0 || timedEvents().length > 0}>
            <SectionHeader label="Events" />
            <For each={allDayEvents()}>
              {(event) => <AllDayEventItem event={event} />}
            </For>
            <For each={timedEvents()}>
              {(event) => <TimedEventItem event={event} />}
            </For>
          </Show>

          {/* Scheduled tasks */}
          <Show when={task().length > 0}>
            <SectionHeader label="Tasks" />
            <For each={task()}>{(task) => <TaskItem task={task} />}</For>
          </Show>
        </main>
      </Show>

      {/* Bottom padding */}
      <div class="h-6" />
    </div>
  );
};

export default DayView;
