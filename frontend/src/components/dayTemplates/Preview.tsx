import { Component, Show, For, createMemo } from "solid-js";
import { DayTemplate, Routine } from "@/types/api";
import { Icon } from "@/components/shared/Icon";

interface DayTemplatePreviewProps {
  dayTemplate: DayTemplate;
  routines?: Routine[];
  onAddRoutine?: (routineId: string) => void;
  onRemoveRoutine?: (routineId: string) => void;
  isEditMode?: boolean;
  isLoading?: boolean;
  error?: string;
}

const DayTemplatePreview: Component<DayTemplatePreviewProps> = (props) => {
  const attachedRoutineIds = createMemo(() => new Set(props.dayTemplate.routine_ids ?? []));

  const attachedRoutines = createMemo(() =>
    (props.routines ?? []).filter((routine) => routine.id && attachedRoutineIds().has(routine.id))
  );

  const availableRoutines = createMemo(() =>
    (props.routines ?? []).filter((routine) => !routine.id || !attachedRoutineIds().has(routine.id))
  );

  return (
    <div class="flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-3xl space-y-8">
        {/* Basic Info */}
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Basic Information</h2>
          <div class="space-y-3">
            <div>
              <label class="text-sm font-medium text-neutral-500">Slug</label>
              <div class="mt-1 text-base text-neutral-900">{props.dayTemplate.slug}</div>
            </div>
            <Show when={props.dayTemplate.icon}>
              <div>
                <label class="text-sm font-medium text-neutral-500">Icon</label>
                <div class="mt-1 text-base text-neutral-900">{props.dayTemplate.icon}</div>
              </div>
            </Show>
          </div>
        </div>

        {/* Routines */}
        <div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-medium text-neutral-900">Routines</h2>
              <p class="text-sm text-neutral-500">
                Routines attached to this day template.
              </p>
            </div>
            <Show when={props.isEditMode}>
              <div class="flex items-center gap-2 text-sm text-neutral-500">
                <Icon key="info" class="w-4 h-4" />
                <span>Click a routine to remove</span>
              </div>
            </Show>
          </div>

          <Show
            when={attachedRoutines().length > 0}
            fallback={<div class="text-sm text-neutral-500">No routines attached yet.</div>}
          >
            <div class="space-y-3">
              <For each={attachedRoutines()}>
                {(routine) => (
                  <div class="flex items-start justify-between rounded-md border border-neutral-200 px-3 py-2">
                    <div class="space-y-1">
                      <div class="text-sm font-medium text-neutral-900">{routine.name}</div>
                      <div class="text-xs text-neutral-500">
                        {routine.description || "No description"}
                      </div>
                    </div>
                    <Show when={props.isEditMode && props.onRemoveRoutine}>
                      <button
                        class="text-sm text-red-600 hover:text-red-700"
                        onClick={() => routine.id && props.onRemoveRoutine?.(routine.id)}
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

          <Show when={props.isEditMode && props.onAddRoutine}>
            <div class="space-y-3">
              <div class="text-sm font-medium text-neutral-900">Add routine</div>
              <Show
                when={availableRoutines().length > 0}
                fallback={<div class="text-sm text-neutral-500">All routines attached.</div>}
              >
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <For each={availableRoutines()}>
                    {(routine) => (
                      <button
                        class="flex items-center justify-between rounded-md border border-neutral-200 px-3 py-2 text-left hover:border-neutral-300 hover:bg-neutral-50"
                        onClick={() => routine.id && props.onAddRoutine?.(routine.id)}
                        disabled={props.isLoading}
                      >
                        <span class="text-sm text-neutral-800">{routine.name}</span>
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
      </div>
    </div>
  );
};

export default DayTemplatePreview;

