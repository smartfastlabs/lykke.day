import {
  Component,
  createSignal,
  createMemo,
  For,
  Show,
  Accessor,
} from "solid-js";
import { createStore } from "solid-js/store";

import { Icon } from "../shared/icon";
import TaskList from "../tasks/list";
import { formatTimeString } from "../tasks/list";
import EventList from "../events/list";
import {
  TaskStatus,
  TaskCategory,
  TaskType,
  TaskFrequency,
} from "../../types/api";

// Constants
const ALL_STATUSES: TaskStatus[] = ["READY", "COMPLETE", "NOT_READY", "PUNTED"];
const ALL_CATEGORIES: TaskCategory[] = [
  "HYGIENE",
  "NUTRITION",
  "HEALTH",
  "PET",
  "HOUSE",
];
const ALL_TYPES: TaskType[] = ["MEAL", "EVENT", "CHORE", "ERRAND", "ACTIVITY"];
const ALL_FREQUENCIES: TaskFrequency[] = [
  "DAILY",
  "WEEKLY",
  "BI_WEEKLY",
  "MONTHLY",
  "YEARLY",
  "ONCE",
  "WORK_DAYS",
  "WEEKENDS",
  "CUSTOM_WEEKLY",
];

// Helper to format labels
const formatLabel = (str: string) =>
  str
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

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

// Filter Chip Component
const FilterChip: Component<{
  label: string;
  active: boolean;
  onClick: () => void;
}> = (props) => (
  <button
    class={`px-2.5 py-1 text-xs rounded-full border transition-all ${
      props.active
        ? "bg-gray-700 text-white border-gray-700"
        : "bg-white text-gray-400 border-gray-200 hover:border-gray-400 hover:text-gray-600"
    }`}
    onClick={props.onClick}
  >
    {props.label}
  </button>
);

// Filter Group Component
const FilterGroup: Component<{
  label: string;
  children: any;
}> = (props) => (
  <div class="py-2">
    <div class="text-[10px] uppercase tracking-wider text-gray-400 mb-2">
      {props.label}
    </div>
    <div class="flex flex-wrap gap-1.5">{props.children}</div>
  </div>
);

// Filter Panel Component
const TaskFilters: Component<{
  filters: {
    statuses: TaskStatus[];
    categories: TaskCategory[];
    types: TaskType[];
    frequencies: TaskFrequency[];
  };
  onToggle: (
    type: "statuses" | "categories" | "types" | "frequencies",
    value: string
  ) => void;
}> = (props) => {
  const [expanded, setExpanded] = createSignal(false);

  const activeCount = () => {
    const defaultStatuses = 1; // READY only
    const defaultOthers =
      ALL_CATEGORIES.length + ALL_TYPES.length + ALL_FREQUENCIES.length;
    const current =
      props.filters.statuses.length +
      props.filters.categories.length +
      props.filters.types.length +
      props.filters.frequencies.length;
    const diff = Math.abs(current - (defaultStatuses + defaultOthers));
    return diff;
  };

  return (
    <div class="border-b border-gray-100">
      {/* Toggle Button */}
      <button
        class="w-full px-5 py-2.5 flex items-center justify-between text-gray-500 hover:text-gray-700 transition-colors"
        onClick={() => setExpanded(!expanded())}
      >
        <div class="flex items-center gap-2">
          <svg
            class={`w-4 h-4 transition-transform ${expanded() ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
            />
          </svg>
          <span class="text-xs uppercase tracking-wider">Filters</span>
        </div>
        <Show when={activeCount() > 0}>
          <span class="text-[10px] bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded-full">
            {activeCount()} changed
          </span>
        </Show>
      </button>

      {/* Expanded Filters */}
      <Show when={expanded()}>
        <div class="px-5 pb-3 space-y-1 border-t border-gray-50">
          <FilterGroup label="Status">
            <For each={ALL_STATUSES}>
              {(status) => (
                <FilterChip
                  label={formatLabel(status)}
                  active={props.filters.statuses.includes(status)}
                  onClick={() => props.onToggle("statuses", status)}
                />
              )}
            </For>
          </FilterGroup>

          <FilterGroup label="Category">
            <For each={ALL_CATEGORIES}>
              {(category) => (
                <FilterChip
                  label={formatLabel(category)}
                  active={props.filters.categories.includes(category)}
                  onClick={() => props.onToggle("categories", category)}
                />
              )}
            </For>
          </FilterGroup>

          <FilterGroup label="Type">
            <For each={ALL_TYPES}>
              {(type) => (
                <FilterChip
                  label={formatLabel(type)}
                  active={props.filters.types.includes(type)}
                  onClick={() => props.onToggle("types", type)}
                />
              )}
            </For>
          </FilterGroup>

          <FilterGroup label="Frequency">
            <For each={ALL_FREQUENCIES}>
              {(freq) => (
                <FilterChip
                  label={formatLabel(freq)}
                  active={props.filters.frequencies.includes(freq)}
                  onClick={() => props.onToggle("frequencies", freq)}
                />
              )}
            </For>
          </FilterGroup>
        </div>
      </Show>
    </div>
  );
};

// Section Header
const SectionHeader: Component<{ label: string }> = (props) => (
  <div class="px-5 py-2 bg-gray-50 border-b border-gray-200">
    <span class="text-xs uppercase tracking-wider text-gray-400">
      {props.label}
    </span>
  </div>
);

// Main DayView Component
interface DayViewProps {
  day: Accessor<Day>;
  events: Accessor<Event[]>;
  tasks: Accessor<Task[]>;
}

const DayView: Component<DayViewProps> = (props) => {
  // Filter state with defaults
  const [filters, setFilters] = createStore({
    statuses: ["READY"] as TaskStatus[],
    categories: [...ALL_CATEGORIES] as TaskCategory[],
    types: [...ALL_TYPES] as TaskType[],
    frequencies: [...ALL_FREQUENCIES] as TaskFrequency[],
  });

  const toggleFilter = (
    type: "statuses" | "categories" | "types" | "frequencies",
    value: string
  ) => {
    const current = filters[type] as string[];
    if (current.includes(value)) {
      // Don't allow removing the last item
      if (current.length > 1) {
        setFilters(type, current.filter((v) => v !== value) as any);
      }
    } else {
      setFilters(type, [...current, value] as any);
    }
  };

  // Filtered tasks
  const filteredTasks = createMemo(() => {
    if (!props.tasks()) return [];

    return props.tasks().filter((task) => {
      const statusMatch = filters.statuses.includes(task.status);
      const categoryMatch = filters.categories.includes(task.category);
      const frequencyMatch = filters.frequencies.includes(task.frequency);
      // Adjust this based on where `type` lives in your Task model
      // Assuming task.task_definition might have a type property
      const typeMatch =
        !task.task_definition?.type ||
        filters.types.includes(task.task_definition.type as TaskType);

      return statusMatch && categoryMatch && frequencyMatch && typeMatch;
    });
  });

  const hasContent = () =>
    (props.events()?.length ?? 0) > 0 || (props.tasks()?.length ?? 0) > 0;

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
            <TaskFilters filters={filters} onToggle={toggleFilter} />
            <Show
              when={filteredTasks().length > 0}
              fallback={
                <div class="px-5 py-8 text-center text-gray-400 text-sm">
                  No tasks match current filters
                </div>
              }
            >
              <TaskList tasks={() => filteredTasks()} />
            </Show>
          </Show>
        </main>
      </Show>

      <div class="h-6" />
    </div>
  );
};

export default DayView;
