import { Component, createSignal, For, Show } from "solid-js";
import { TaskStatus, TaskType } from "@/types/api";
import { FilterChip } from "./FilterChip";
import { FilterGroup } from "./FilterGroup";
import {
  ALL_STATUSES,
  ALL_TYPES,
  FREQUENCY_GROUPS,
  type FrequencyGroup,
  type TaskFiltersState,
  formatLabel,
} from "./types";

interface TaskFiltersProps {
  filters: TaskFiltersState;
  onToggleStatus: (value: string) => void;
  onToggleType: (value: string) => void;
  onToggleFrequencyGroup: (value: FrequencyGroup | "ALL") => void;
}

export const TaskFilters: Component<TaskFiltersProps> = (props) => {
  const [expanded, setExpanded] = createSignal(false);

  return (
    <div class="mb-4">
      {/* Toggle Button */}
      <button
        class="w-full px-0 py-2.5 flex items-center justify-between text-stone-500 hover:text-stone-700 transition-colors"
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
        <div class="px-0 pb-3 space-y-1">
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
                      ? props.filters.frequencyGroups.length === FREQUENCY_GROUPS.length
                      : props.filters.frequencyGroups.includes(group as FrequencyGroup)
                  }
                  onClick={() => props.onToggleFrequencyGroup(group as FrequencyGroup | "ALL")}
                />
              )}
            </For>
          </FilterGroup>
        </div>
      </Show>
    </div>
  );
};

