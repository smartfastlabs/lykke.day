import { Component, Show, For, createMemo, createResource, createSignal } from "solid-js";
import { DayTemplate, RoutineDefinition, TimeBlockDefinition } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import { timeBlockDefinitionAPI } from "@/utils/api";

interface DayTemplatePreviewProps {
  dayTemplate: DayTemplate;
  routineDefinitions?: RoutineDefinition[];
  onAddRoutineDefinition?: (routineDefinitionId: string) => void;
  onRemoveRoutineDefinition?: (routineDefinitionId: string) => void;
  onAddTimeBlock?: (timeBlockDefinitionId: string, startTime: string, endTime: string) => void;
  onRemoveTimeBlock?: (timeBlockDefinitionId: string, startTime: string) => void;
  isEditMode?: boolean;
  isLoading?: boolean;
  error?: string;
}

const DayTemplatePreview: Component<DayTemplatePreviewProps> = (props) => {
  const [timeBlockDefinitions] = createResource<TimeBlockDefinition[]>(
    timeBlockDefinitionAPI.getAll
  );
  const [selectedTimeBlockDefId, setSelectedTimeBlockDefId] = createSignal<string>("");
  const [startTime, setStartTime] = createSignal<string>("09:00");
  const [endTime, setEndTime] = createSignal<string>("10:00");
  const hasHighLevelPlan = createMemo(
    () =>
      Boolean(
        props.dayTemplate.high_level_plan?.title ||
          props.dayTemplate.high_level_plan?.text ||
          (props.dayTemplate.high_level_plan?.intentions &&
            props.dayTemplate.high_level_plan.intentions.length > 0)
      )
  );

  const attachedRoutineDefinitionIds = createMemo(
    () => new Set(props.dayTemplate.routine_definition_ids ?? [])
  );

  const attachedRoutineDefinitions = createMemo(() =>
    (props.routineDefinitions ?? []).filter(
      (routineDefinition) =>
        routineDefinition.id &&
        attachedRoutineDefinitionIds().has(routineDefinition.id)
    )
  );

  const availableRoutineDefinitions = createMemo(() =>
    (props.routineDefinitions ?? []).filter(
      (routineDefinition) =>
        !routineDefinition.id ||
        !attachedRoutineDefinitionIds().has(routineDefinition.id)
    )
  );


  const formatTime = (time: string): string => {
    // time is in HH:MM:SS format, return HH:MM
    return time.substring(0, 5);
  };

  const handleAddTimeBlock = () => {
    const defId = selectedTimeBlockDefId();
    if (!defId || !startTime() || !endTime()) return;
    
    // Convert HH:MM to HH:MM:SS format
    const start = `${startTime()}:00`;
    const end = `${endTime()}:00`;
    
    props.onAddTimeBlock?.(defId, start, end);
    
    // Reset form
    setSelectedTimeBlockDefId("");
    setStartTime("09:00");
    setEndTime("10:00");
  };

  return (
    <div class="space-y-8">
      {/* High Level Plan */}
      <Show when={hasHighLevelPlan() && props.dayTemplate.high_level_plan}>
        {(plan) => (
          <div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-3">
            <div>
              <h2 class="text-lg font-medium text-neutral-900">High Level Plan</h2>
              <p class="text-sm text-neutral-500">
                The guiding intention for this template.
              </p>
            </div>
            <Show when={plan().title}>
              <div class="text-sm font-semibold text-neutral-800">
                {plan().title}
              </div>
            </Show>
            <Show when={plan().text}>
              <p class="text-sm text-neutral-600 whitespace-pre-line">
                {plan().text}
              </p>
            </Show>
            <Show when={(plan().intentions?.length ?? 0) > 0}>
              <div class="space-y-2">
                <div class="text-xs font-medium text-neutral-700">Intentions</div>
                <ul class="space-y-1">
                  <For each={plan().intentions}>
                    {(intention) => (
                      <li class="text-sm text-neutral-600 bg-neutral-50 rounded-lg px-3 py-2">
                        {intention}
                      </li>
                    )}
                  </For>
                </ul>
              </div>
            </Show>
          </div>
        )}
      </Show>
      {/* Routine Definitions */}
      <div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-medium text-neutral-900">
                Routine Definitions
              </h2>
              <p class="text-sm text-neutral-500">
                Routine definitions attached to this day template.
              </p>
            </div>
            <Show when={props.isEditMode}>
              <div class="flex items-center gap-2 text-sm text-neutral-500">
                <Icon key="info" class="w-4 h-4" />
                <span>Click a routine definition to remove</span>
              </div>
            </Show>
          </div>

          <Show
            when={attachedRoutineDefinitions().length > 0}
            fallback={
              <div class="text-sm text-neutral-500">
                No routine definitions attached yet.
              </div>
            }
          >
            <div class="space-y-3">
              <For each={attachedRoutineDefinitions()}>
                {(routineDefinition) => (
                  <div class="flex items-start justify-between rounded-md border border-neutral-200 px-3 py-2">
                    <div class="space-y-1">
                      <div class="text-sm font-medium text-neutral-900">
                        {routineDefinition.name}
                      </div>
                      <div class="text-xs text-neutral-500">
                        {routineDefinition.description || "No description"}
                      </div>
                    </div>
                    <Show
                      when={props.isEditMode && props.onRemoveRoutineDefinition}
                    >
                      <button
                        class="text-sm text-red-600 hover:text-red-700"
                        onClick={() =>
                          routineDefinition.id &&
                          props.onRemoveRoutineDefinition?.(
                            routineDefinition.id
                          )
                        }
                        disabled={props.isLoading}
                      >
                        Remove
                      </button>
                    </Show>
                  </div>
                )}
              </For>
            </div>
          </Show>

          <Show when={props.isEditMode && props.onAddRoutineDefinition}>
            <div class="space-y-3">
              <div class="text-sm font-medium text-neutral-900">
                Add routine definition
              </div>
              <Show
                when={availableRoutineDefinitions().length > 0}
                fallback={
                  <div class="text-sm text-neutral-500">
                    All routine definitions attached.
                  </div>
                }
              >
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <For each={availableRoutineDefinitions()}>
                    {(routineDefinition) => (
                      <button
                        class="flex items-center justify-between rounded-md border border-neutral-200 px-3 py-2 text-left hover:border-neutral-300 hover:bg-neutral-50"
                        onClick={() =>
                          routineDefinition.id &&
                          props.onAddRoutineDefinition?.(
                            routineDefinition.id
                          )
                        }
                        disabled={props.isLoading}
                      >
                        <span class="text-sm text-neutral-800">
                          {routineDefinition.name}
                        </span>
                        <Icon key="plus" class="w-4 h-4 text-neutral-500" />
                      </button>
                    )}
                  </For>
                </div>
              </Show>
            </div>
          </Show>

          <Show when={props.error}>
            <div class="text-sm text-red-600">{props.error}</div>
          </Show>
        </div>

        {/* Time Blocks */}
        <div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-medium text-neutral-900">Time Blocks</h2>
              <p class="text-sm text-neutral-500">
                Time blocks scheduled in this day template.
              </p>
            </div>
            <Show when={props.isEditMode}>
              <div class="flex items-center gap-2 text-sm text-neutral-500">
                <Icon key="info" class="w-4 h-4" />
                <span>Click a time block to remove</span>
              </div>
            </Show>
          </div>

          <Show
            when={(props.dayTemplate.time_blocks ?? []).length > 0}
            fallback={<div class="text-sm text-neutral-500">No time blocks added yet.</div>}
          >
            <div class="space-y-3">
              <For each={props.dayTemplate.time_blocks ?? []}>
                {(timeBlock) => {
                  return (
                    <div class="flex items-start justify-between rounded-md border border-neutral-200 px-3 py-2">
                      <div class="space-y-1">
                        <div class="text-sm font-medium text-neutral-900">
                          {timeBlock.name}
                        </div>
                        <div class="text-xs text-neutral-500">
                          {formatTime(timeBlock.start_time)} - {formatTime(timeBlock.end_time)}
                        </div>
                      </div>
                      <Show when={props.isEditMode && props.onRemoveTimeBlock}>
                        <button
                          class="text-sm text-red-600 hover:text-red-700"
                          onClick={() =>
                            props.onRemoveTimeBlock?.(
                              timeBlock.time_block_definition_id,
                              timeBlock.start_time
                            )
                          }
                          disabled={props.isLoading}
                        >
                          Remove
                        </button>
                      </Show>
                    </div>
                  );
                }}
              </For>
            </div>
          </Show>

          <Show when={props.isEditMode && props.onAddTimeBlock}>
            <div class="space-y-3">
              <div class="text-sm font-medium text-neutral-900">Add time block</div>
              <Show
                when={timeBlockDefinitions() && timeBlockDefinitions()!.length > 0}
                fallback={
                  <div class="text-sm text-neutral-500">
                    No time block definitions available. Create one first.
                  </div>
                }
              >
                <div class="space-y-3">
                  <div>
                    <label class="text-xs text-neutral-500 mb-1 block">
                      Time Block Definition
                    </label>
                    <select
                      class="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                      value={selectedTimeBlockDefId()}
                      onChange={(e) => setSelectedTimeBlockDefId(e.currentTarget.value)}
                    >
                      <option value="">Select a time block definition...</option>
                      <For each={timeBlockDefinitions()}>
                        {(def) => (
                          <option value={def.id ?? undefined}>
                            {def.name} ({def.type})
                          </option>
                        )}
                      </For>
                    </select>
                  </div>
                  <div class="grid grid-cols-2 gap-3">
                    <div>
                      <label class="text-xs text-neutral-500 mb-1 block">
                        Start Time
                      </label>
                      <input
                        type="time"
                        class="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                        value={startTime()}
                        onChange={(e) => setStartTime(e.currentTarget.value)}
                      />
                    </div>
                    <div>
                      <label class="text-xs text-neutral-500 mb-1 block">
                        End Time
                      </label>
                      <input
                        type="time"
                        class="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                        value={endTime()}
                        onChange={(e) => setEndTime(e.currentTarget.value)}
                      />
                    </div>
                  </div>
                  <button
                    class="w-full rounded-md bg-neutral-900 px-4 py-2 text-sm text-white hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed"
                    onClick={handleAddTimeBlock}
                    disabled={!selectedTimeBlockDefId() || props.isLoading}
                  >
                    Add Time Block
                  </button>
                </div>
              </Show>
            </div>
          </Show>

          <Show when={props.error}>
            <div class="text-sm text-red-600">{props.error}</div>
          </Show>
        </div>

        {/* Alarms */}
        <div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-4">
          <div>
            <h2 class="text-lg font-medium text-neutral-900">Alarms</h2>
            <p class="text-sm text-neutral-500">
              Alarm cues that will appear on scheduled days.
            </p>
          </div>
          <Show
            when={(props.dayTemplate.alarms ?? []).length > 0}
            fallback={<div class="text-sm text-neutral-500">No alarms added yet.</div>}
          >
            <div class="space-y-3">
              <For each={props.dayTemplate.alarms ?? []}>
                {(alarm) => (
                  <div class="flex items-center justify-between rounded-md border border-neutral-200 px-3 py-2">
                    <div class="space-y-1">
                      <div class="text-sm font-medium text-neutral-900">
                        {alarm.name}
                      </div>
                      <div class="text-xs text-neutral-500">
                        {formatTime(alarm.time)} · {alarm.type}
                      </div>
                    </div>
                    <Show when={alarm.url}>
                      <a
                        class="text-xs text-neutral-500 hover:text-neutral-700"
                        href={alarm.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Link
                      </a>
                    </Show>
                  </div>
                )}
              </For>
            </div>
          </Show>
        </div>
    </div>
  );
};

export default DayTemplatePreview;

