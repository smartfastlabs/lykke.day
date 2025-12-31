import { Component, createMemo, Show, type Accessor } from "solid-js";
import { createStore } from "solid-js/store";

import TaskList from "../tasks/list";
import EventList from "../events/list";
import { EmptyState } from "../shared/EmptyState";
import { SectionHeader } from "../shared/SectionHeader";
import {
  TaskFilters,
  ALL_STATUSES,
  ALL_TYPES,
  FREQUENCY_GROUPS,
  frequencyGroupMap,
  type FrequencyGroup,
  type TaskFiltersState,
} from "./filters";
import { TaskStatus, TaskType, TaskFrequency, Task, Event } from "../../types/api";

interface DayViewProps {
  events: Accessor<Event[]>;
  tasks: Accessor<Task[]>;
}

const DayView: Component<DayViewProps> = (props) => {
  // Filter state with defaults
  const [filters, setFilters] = createStore<TaskFiltersState>({
    statuses: [...ALL_STATUSES],
    types: [...ALL_TYPES],
    frequencyGroups: [...FREQUENCY_GROUPS],
  });

  const toggleStatus = (value: string) => {
    if (value === "ALL") {
      setFilters("statuses", filters.statuses.length === ALL_STATUSES.length ? [] : [...ALL_STATUSES]);
    } else {
      const current = filters.statuses;
      if (current.includes(value as TaskStatus)) {
        if (current.length > 1) {
          setFilters("statuses", current.filter((v) => v !== value));
        }
      } else {
        setFilters("statuses", [...current, value as TaskStatus]);
      }
    }
  };

  const toggleType = (value: string) => {
    if (value === "ALL") {
      setFilters("types", filters.types.length === ALL_TYPES.length ? [] : [...ALL_TYPES]);
    } else {
      const current = filters.types;
      if (current.includes(value as TaskType)) {
        if (current.length > 1) {
          setFilters("types", current.filter((v) => v !== value));
        }
      } else {
        setFilters("types", [...current, value as TaskType]);
      }
    }
  };

  const toggleFrequencyGroup = (value: FrequencyGroup | "ALL") => {
    if (value === "ALL") {
      setFilters(
        "frequencyGroups",
        filters.frequencyGroups.length === FREQUENCY_GROUPS.length ? [] : [...FREQUENCY_GROUPS]
      );
    } else {
      const current = filters.frequencyGroups;
      if (current.includes(value)) {
        if (current.length > 1) {
          setFilters("frequencyGroups", current.filter((v) => v !== value));
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
    const tasks = props.tasks();
    if (!tasks) return [];

    return tasks.filter((task) => {
      const statusMatch = filters.statuses.includes(task.status);
      const frequencyMatch = allowedFrequencies().includes(task.frequency);
      const typeMatch =
        !task.task_definition?.type ||
        filters.types.includes(task.task_definition.type as TaskType);

      return statusMatch && frequencyMatch && typeMatch;
    });
  });

  const hasContent = () => {
    const events = props.events();
    const tasks = props.tasks();
    return (events?.length ?? 0) > 0 || (tasks?.length ?? 0) > 0;
  };

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
