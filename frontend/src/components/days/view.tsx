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
import { TaskStatus, TaskType, TaskFrequency } from "../../types/api";

// Constants
const ALL_STATUSES: TaskStatus[] = [
  "READY",
  "COMPLETE",
  "NOT_READY",
  "PUNT",
  "NOT_STARTED",
  "PENDING",
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

// Frequency display groups for the simplified filter
type FrequencyGroup = "ONCE" | "DAILY" | "WEEKLY" | "MONTHLY+";
const FREQUENCY_GROUPS: FrequencyGroup[] = [
  "ONCE",
  "DAILY",
  "WEEKLY",
  "MONTHLY+",
];

// Map frequency groups to actual TaskFrequency values
const frequencyGroupMap: Record<FrequencyGroup, TaskFrequency[]> = {
  ONCE: ["ONCE"],
  DAILY: ["DAILY", "WORK_DAYS", "WEEKENDS"],
  WEEKLY: ["WEEKLY", "BI_WEEKLY", "CUSTOM_WEEKLY"],
  "MONTHLY+": ["MONTHLY", "YEARLY"],
};

// Helper to format labels
const formatLabel = (str: string) =>
  str
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

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
    types: TaskType[];
    frequencyGroups: FrequencyGroup[];
  };
  onToggleStatus: (value: string) => void;
  onToggleType: (value: string) => void;
  onToggleFrequencyGroup: (value: FrequencyGroup) => void;
}> = (props) => {
  const [expanded, setExpanded] = createSignal(false);

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
      </button>

      {/* Expanded Filters */}
      <Show when={expanded()}>
        <div class="px-5 pb-3 space-y-1 border-t border-gray-50">
          <FilterGroup label="Status">
            <For each={["ALL", ...ALL_STATUSES]}>
              {(status) => (
                <FilterChip
                  label={formatLabel(status)}
                  active={
                    status === "ALL"
                      ? props.filters.statuses.length === ALL_STATUSES.length
                      : props.filters.statuses.includes(status as TaskStatus)
                  }
                  onClick={() => props.onToggleStatus(status)}
                />
              )}
            </For>
          </FilterGroup>

          <FilterGroup label="Type">
            <For each={["ALL", ...ALL_TYPES]}>
              {(type) => (
                <FilterChip
                  label={formatLabel(type)}
                  active={
                    type === "ALL"
                      ? props.filters.types.length === ALL_TYPES.length
                      : props.filters.types.includes(type as TaskType)
                  }
                  onClick={() => props.onToggleType(type)}
                />
              )}
            </For>
          </FilterGroup>

          <FilterGroup label="Frequency">
            <For each={["ALL", ...FREQUENCY_GROUPS]}>
              {(group) => (
                <FilterChip
                  label={group === "ALL" ? "All" : group}
                  active={
                    group === "ALL"
                      ? props.filters.frequencyGroups.length ===
                        FREQUENCY_GROUPS.length
                      : props.filters.frequencyGroups.includes(
                          group as FrequencyGroup
                        )
                  }
                  onClick={() =>
                    props.onToggleFrequencyGroup(
                      group as FrequencyGroup | "ALL"
                    )
                  }
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
    statuses: [...ALL_STATUSES] as TaskStatus[],
    types: [...ALL_TYPES] as TaskType[],
    frequencyGroups: [...FREQUENCY_GROUPS] as FrequencyGroup[],
  });

  const toggleStatus = (value: string) => {
    if (value === "ALL") {
      if (filters.statuses.length === ALL_STATUSES.length) {
        setFilters("statuses", []);
      } else {
        setFilters("statuses", [...ALL_STATUSES]);
      }
    } else {
      const current = filters.statuses;
      if (current.includes(value as TaskStatus)) {
        if (current.length > 1) {
          setFilters(
            "statuses",
            current.filter((v) => v !== value)
          );
        }
      } else {
        setFilters("statuses", [...current, value as TaskStatus]);
      }
    }
  };

  const toggleType = (value: string) => {
    if (value === "ALL") {
      if (filters.types.length === ALL_TYPES.length) {
        setFilters("types", []);
      } else {
        setFilters("types", [...ALL_TYPES]);
      }
    } else {
      const current = filters.types;
      if (current.includes(value as TaskType)) {
        if (current.length > 1) {
          setFilters(
            "types",
            current.filter((v) => v !== value)
          );
        }
      } else {
        setFilters("types", [...current, value as TaskType]);
      }
    }
  };

  const toggleFrequencyGroup = (value: FrequencyGroup | "ALL") => {
    if (value === "ALL") {
      if (filters.frequencyGroups.length === FREQUENCY_GROUPS.length) {
        setFilters("frequencyGroups", []);
      } else {
        setFilters("frequencyGroups", [...FREQUENCY_GROUPS]);
      }
    } else {
      const current = filters.frequencyGroups;
      if (current.includes(value)) {
        if (current.length > 1) {
          setFilters(
            "frequencyGroups",
            current.filter((v) => v !== value)
          );
        }
      } else {
        setFilters("frequencyGroups", [...current, value]);
      }
    }
  };

  // Get all allowed frequencies based on selected groups
  const allowedFrequencies = createMemo(() => {
    const frequencies: TaskFrequency[] = [];
    for (const group of filters.frequencyGroups) {
      frequencies.push(...frequencyGroupMap[group]);
    }
    return frequencies;
  });

  // Filtered tasks
  const filteredTasks = createMemo(() => {
    if (!props.tasks()) return [];

    return props.tasks().filter((task) => {
      const statusMatch = filters.statuses.includes(task.status);
      const frequencyMatch = allowedFrequencies().includes(task.frequency);
      const typeMatch =
        !task.task_definition?.type ||
        filters.types.includes(task.task_definition.type as TaskType);

      return statusMatch && frequencyMatch && typeMatch;
    });
  });

  const hasContent = () =>
    (props.events()?.length ?? 0) > 0 || (props.tasks()?.length ?? 0) > 0;

  return (
    <div class="min-h-screen bg-white">
      <Show when={hasContent()} fallback={<EmptyState />}>
        <main>
          <Show when={props.events()?.length}>
            <SectionHeader label="Events" />
            <EventList events={props.events} />
          </Show>

          <Show when={props.tasks()?.length}>
            <SectionHeader label="Tasks" />
            <TaskFilters
              filters={filters}
              onToggleStatus={toggleStatus}
              onToggleType={toggleType}
              onToggleFrequencyGroup={toggleFrequencyGroup}
            />
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
