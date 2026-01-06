import { Component, Show, For, createMemo } from "solid-js";
import { Routine, RoutineTask, TaskDefinition, TaskSchedule } from "@/types/api";
import { Icon } from "@/components/shared/icon";
import TaskScheduleForm from "@/components/tasks/scheduleForm";
import { Input } from "@/components/forms";

interface RoutinePreviewProps {
  routine: Routine;
  taskDefinitions?: TaskDefinition[];
  onAddTask?: (taskDef: TaskDefinition) => void;
  onEditTask?: (task: RoutineTask) => void;
  onRemoveTask?: (taskDefinitionId: string) => void;
  onTaskSubmit?: (schedule: TaskSchedule) => void;
  onTaskCancel?: () => void;
  selectedTaskDefinitionId?: () => string | null;
  selectedAction?: () => "add" | "edit" | null;
  taskName?: () => string;
  setTaskName?: (name: string) => void;
  scheduleInitial?: () => TaskSchedule | null;
  isEditMode?: boolean;
  isLoading?: boolean;
  error?: string;
}

const RoutinePreview: Component<RoutinePreviewProps> = (props) => {
  const attachedTasks = createMemo(() => props.routine.tasks ?? []);

  const attachedTaskIds = createMemo(
    () => new Set(attachedTasks().map((task) => task.task_definition_id))
  );

  const availableDefinitions = createMemo(() =>
    (props.taskDefinitions ?? []).filter((def) => !attachedTaskIds().has(def.id!))
  );

  const getTaskDefinitionName = (taskDefinitionId: string) =>
    props.taskDefinitions?.find((def) => def.id === taskDefinitionId)?.name ?? taskDefinitionId;

  return (
    <div class="flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-3xl space-y-8">
        {/* Basic Info */}
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Basic Information</h2>
          <div class="space-y-3">
            <div>
              <label class="text-sm font-medium text-neutral-500">Name</label>
              <div class="mt-1 text-base text-neutral-900">{props.routine.name}</div>
            </div>
            <Show when={props.routine.description}>
              <div>
                <label class="text-sm font-medium text-neutral-500">Description</label>
                <div class="mt-1 text-base text-neutral-900">{props.routine.description}</div>
              </div>
            </Show>
            <div>
              <label class="text-sm font-medium text-neutral-500">Category</label>
              <div class="mt-1 text-base text-neutral-900">{props.routine.category}</div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Frequency</label>
              <div class="mt-1 text-base text-neutral-900">
                {props.routine.routine_schedule.frequency}
              </div>
            </div>
          </div>
        </div>

        {/* Routine Tasks */}
        <div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-medium text-neutral-900">Routine Tasks</h2>
              <p class="text-sm text-neutral-500">Tasks attached to this routine.</p>
            </div>
            <Show when={props.isEditMode}>
              <div class="flex items-center gap-2 text-sm text-neutral-500">
                <Icon key="info" class="w-4 h-4" />
                <span>Click a task to edit or remove</span>
              </div>
            </Show>
          </div>

          <Show
            when={attachedTasks().length > 0}
            fallback={<div class="text-sm text-neutral-500">No tasks attached yet.</div>}
          >
            <div class="space-y-3">
              <For each={attachedTasks()}>
                {(task) => (
                  <div class="flex items-start justify-between rounded-md border border-neutral-200 px-3 py-2">
                    <div class="space-y-1">
                      <div class="text-sm font-medium text-neutral-900">
                        {task.name || getTaskDefinitionName(task.task_definition_id)}
                      </div>
                      <div class="text-xs text-neutral-500">
                        {task.schedule
                          ? `${task.schedule.timing_type}${
                              task.schedule.start_time ? ` • ${task.schedule.start_time}` : ""
                            }${
                              task.schedule.end_time ? ` - ${task.schedule.end_time}` : ""
                            }`
                          : "No schedule set"}
                      </div>
                    </div>
                    <Show when={props.isEditMode}>
                      <div class="flex items-center gap-2">
                        <Show when={props.onEditTask}>
                          <button
                            class="text-sm text-blue-600 hover:text-blue-700"
                            onClick={() => props.onEditTask?.(task)}
                            disabled={props.isLoading}
                          >
                            Edit
                          </button>
                        </Show>
                        <Show when={props.onRemoveTask}>
                          <button
                            class="text-sm text-red-600 hover:text-red-700"
                            onClick={() => props.onRemoveTask?.(task.task_definition_id)}
                            disabled={props.isLoading}
                          >
                            Remove
                          </button>
                        </Show>
                      </div>
                    </Show>
                  </div>
                )}
              </For>
            </div>
          </Show>

          <Show when={props.isEditMode && props.onAddTask}>
            <div class="space-y-3">
              <div class="text-sm font-medium text-neutral-900">Add task</div>
              <Show
                when={availableDefinitions().length > 0}
                fallback={<div class="text-sm text-neutral-500">All tasks attached.</div>}
              >
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <For each={availableDefinitions()}>
                    {(def) => (
                      <button
                        class="flex items-center justify-between rounded-md border border-neutral-200 px-3 py-2 text-left hover:border-neutral-300 hover:bg-neutral-50"
                        onClick={() => props.onAddTask?.(def)}
                        disabled={props.isLoading}
                      >
                        <span class="text-sm text-neutral-800">{def.name}</span>
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

          <Show
            when={
              props.selectedAction?.() && props.onTaskSubmit && props.onTaskCancel
            }
          >
            <div class="mt-4 rounded-md border border-neutral-200 bg-neutral-50 p-4 space-y-3">
              <div class="flex items-center justify-between">
                <div>
                  <div class="text-sm font-medium text-neutral-900">
                    {props.selectedAction?.() === "add" ? "Add Task" : "Edit Task"}
                  </div>
                  <div class="text-xs text-neutral-500">
                    {getTaskDefinitionName(props.selectedTaskDefinitionId?.() ?? "")}
                  </div>
                </div>
                <button
                  type="button"
                  class="text-xs text-neutral-500 hover:text-neutral-700"
                  onClick={() => props.onTaskCancel?.()}
                >
                  Cancel
                </button>
              </div>

              <Show when={props.setTaskName && props.taskName}>
                <Input
                  id="routine_task_name"
                  placeholder="Task name (optional)"
                  value={props.taskName!}
                  onChange={props.setTaskName!}
                />
              </Show>

              <Show when={props.onTaskSubmit}>
                <TaskScheduleForm
                  initialSchedule={props.scheduleInitial?.() ?? undefined}
                  onSubmit={props.onTaskSubmit!}
                  onCancel={() => props.onTaskCancel?.()}
                  isLoading={props.isLoading}
                  submitText={props.selectedAction?.() === "add" ? "Attach Task" : "Save"}
                />
              </Show>

              <Show when={props.error}>
                <div class="text-sm text-red-600">{props.error}</div>
              </Show>
            </div>
          </Show>
        </div>
      </div>
    </div>
  );
};

export default RoutinePreview;

