import { Component, Show, For, createMemo, Setter, Accessor, createSignal, createEffect } from "solid-js";
import {
  RecurrenceSchedule,
  RoutineDefinition,
  RoutineDefinitionTask,
  TaskDefinition,
  TaskSchedule,
  TaskType,
  TimeWindow,
} from "@/types/api";
import { ALL_TASK_TYPES } from "@/types/api/constants";
import { Icon } from "@/components/shared/Icon";
import TaskScheduleForm from "@/components/tasks/ScheduleForm";
import RoutineScheduleForm from "@/components/routine-definitions/RoutineScheduleForm";
import { Input, Button, Select, TextArea } from "@/components/forms";

interface RoutinePreviewProps {
  routineDefinition: RoutineDefinition;
  taskDefinitions?: TaskDefinition[];
  onAddTask?: (taskDef: TaskDefinition) => void;
  onCreateTaskDefinition?: (taskDef: TaskDefinition) => Promise<void>;
  onEditTask?: (task: RoutineDefinitionTask) => void;
  onRemoveTask?: (taskDefinitionId: string) => void;
  onTaskSubmit?: (
    schedule: TaskSchedule,
    taskSchedule: RecurrenceSchedule | null,
    timeWindow: TimeWindow | null
  ) => Promise<void>;
  onTaskCancel?: () => void;
  selectedTaskDefinitionId?: () => string | null;
  selectedAction?: () => "add" | "edit" | null;
  taskName?: Accessor<string>;
  setTaskName?: Setter<string>;
  scheduleInitial?: () => TaskSchedule | null;
  taskScheduleInitial?: () => RecurrenceSchedule | null;
  timeWindowInitial?: () => TimeWindow | null;
  isEditMode?: boolean;
  isLoading?: boolean;
  error?: string;
  showBasicInfo?: boolean;
  layout?: "standalone" | "embedded";
}

const RoutinePreview: Component<RoutinePreviewProps> = (props) => {
  const attachedTasks = createMemo(
    () => props.routineDefinition.tasks ?? []
  );

  const availableDefinitions = createMemo(() => props.taskDefinitions ?? []);
  
  // Track schedule state for the form
  const [currentSchedule, setCurrentSchedule] = createSignal<TaskSchedule | null>(null);
  const [currentTaskSchedule, setCurrentTaskSchedule] = createSignal<RecurrenceSchedule | null>(
    null
  );
  
  // State for creating new task definition
  const [showCreateTaskDef, setShowCreateTaskDef] = createSignal(false);
  const [newTaskDefName, setNewTaskDefName] = createSignal("");
  const [newTaskDefDescription, setNewTaskDefDescription] = createSignal("");
  const [newTaskDefType, setNewTaskDefType] = createSignal<TaskType>("CHORE");
  const [isCreatingTaskDef, setIsCreatingTaskDef] = createSignal(false);
  const [isModalOpen, setIsModalOpen] = createSignal(false);
  const [isPickingTask, setIsPickingTask] = createSignal(false);
  
  // Update schedule state when form opens
  createEffect(() => {
    if (props.selectedAction?.()) {
      const initialSchedule = props.scheduleInitial?.();
      if (initialSchedule) {
        setCurrentSchedule(initialSchedule);
      } else {
        // Initialize with default schedule if adding new task
        setCurrentSchedule({
          timing_type: "FLEXIBLE" as const,
          available_time: null,
          start_time: null,
          end_time: null,
        });
      }
      setCurrentTaskSchedule(props.taskScheduleInitial?.() ?? null);
    }
  });

  createEffect(() => {
    if (props.selectedAction?.()) {
      setIsModalOpen(true);
      setIsPickingTask(false);
    } else if (!isPickingTask()) {
      setIsModalOpen(false);
    }
  });

  const handleCreateTaskDefinition = async () => {
    if (!props.onCreateTaskDefinition) return;
    setIsCreatingTaskDef(true);
    try {
      const newTaskDef: TaskDefinition = {
        name: newTaskDefName().trim(),
        description: newTaskDefDescription().trim(),
        type: newTaskDefType(),
      } as TaskDefinition;
      await props.onCreateTaskDefinition(newTaskDef);
      // Reset form
      setShowCreateTaskDef(false);
      setNewTaskDefName("");
      setNewTaskDefDescription("");
      setNewTaskDefType("CHORE");
    } catch (err) {
      console.error("Failed to create task definition:", err);
    } finally {
      setIsCreatingTaskDef(false);
    }
  };

  const handleTaskSubmit = () => {
    const schedule = currentSchedule() ?? {
      timing_type: "FLEXIBLE" as const,
      available_time: null,
      start_time: null,
      end_time: null,
    };
    const taskSchedule = currentTaskSchedule();
    void props.onTaskSubmit?.(schedule, taskSchedule, null);
  };

  const getTaskDefinitionName = (taskDefinitionId: string) =>
    props.taskDefinitions?.find((def) => def.id === taskDefinitionId)?.name ?? taskDefinitionId;

  const handleOpenAddTask = () => {
    setIsModalOpen(true);
    setIsPickingTask(true);
    setShowCreateTaskDef(false);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setIsPickingTask(false);
    props.onTaskCancel?.();
  };

  const layoutClass = () =>
    props.layout === "embedded"
      ? "space-y-6"
      : "flex flex-col items-center justify-center px-0 py-8";

  return (
    <div class={layoutClass()}>
      <div class={props.layout === "embedded" ? "space-y-6" : "w-full max-w-3xl space-y-8"}>
        <Show when={props.showBasicInfo ?? true}>
          <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
            <h2 class="text-lg font-semibold text-stone-800">Basic Information</h2>
            <div class="space-y-3">
              <div>
                <label class="text-sm font-medium text-neutral-500">Name</label>
                <div class="mt-1 text-base text-neutral-900">
                  {props.routineDefinition.name}
                </div>
              </div>
              <Show when={props.routineDefinition.description}>
                <div>
                  <label class="text-sm font-medium text-neutral-500">Description</label>
                  <div class="mt-1 text-base text-neutral-900">
                    {props.routineDefinition.description}
                  </div>
                </div>
              </Show>
              <div>
                <label class="text-sm font-medium text-neutral-500">Category</label>
                <div class="mt-1 text-base text-neutral-900">
                  {props.routineDefinition.category}
                </div>
              </div>
              <div>
                <label class="text-sm font-medium text-neutral-500">Frequency</label>
                <div class="mt-1 text-base text-neutral-900">
                  {props.routineDefinition.routine_definition_schedule.frequency}
                </div>
              </div>
              <Show when={props.routineDefinition.time_window}>
                <div>
                  <label class="text-sm font-medium text-neutral-500">Time Window</label>
                  <div class="mt-1 text-base text-neutral-900">
                    {props.routineDefinition.time_window?.available_time
                      ? `Preferred ${props.routineDefinition.time_window.available_time}`
                      : "Window"}
                    {props.routineDefinition.time_window?.start_time
                      ? ` • ${props.routineDefinition.time_window.start_time}`
                      : ""}
                    {props.routineDefinition.time_window?.end_time
                      ? ` - ${props.routineDefinition.time_window.end_time}`
                      : ""}
                    {props.routineDefinition.time_window?.cutoff_time
                      ? ` • Cutoff ${props.routineDefinition.time_window.cutoff_time}`
                      : ""}
                  </div>
                </div>
              </Show>
            </div>
          </div>
        </Show>

        {/* Routine Definition Tasks */}
        <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-stone-800">Tasks in this routine</h2>
              <p class="text-sm text-neutral-500">
                Tasks attached to this routine definition.
              </p>
            </div>
            <Show when={props.isEditMode}>
              <button
                type="button"
                class="inline-flex items-center gap-2 rounded-full bg-stone-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={handleOpenAddTask}
                disabled={props.isLoading}
              >
                <Icon key="plus" class="h-4 w-4 text-white" />
                Add task
              </button>
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
                      <div class="text-xs text-neutral-500 space-y-1">
                        {task.schedule && (
                          <div>
                            Time: {task.schedule.timing_type}
                            {task.schedule.start_time ? ` • ${task.schedule.start_time}` : ""}
                            {task.schedule.end_time ? ` - ${task.schedule.end_time}` : ""}
                          </div>
                        )}
                        {task.task_schedule && (
                          <div>
                            Days: {task.task_schedule.frequency}
                            {task.task_schedule.weekdays && task.task_schedule.weekdays.length > 0 && (
                              <span> • {task.task_schedule.weekdays.map(d => ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d]).join(", ")}</span>
                            )}
                          </div>
                        )}
                        {!task.schedule && !task.task_schedule && (
                          <div>No schedule set</div>
                        )}
                      </div>
                    </div>
                    <Show when={props.isEditMode}>
                      <div class="flex items-center gap-2">
                        <Show when={props.onEditTask}>
                          <button
                            class="text-sm text-amber-700 hover:text-amber-800"
                            onClick={() => props.onEditTask?.(task)}
                            disabled={props.isLoading}
                          >
                            Edit
                          </button>
                        </Show>
                        <Show when={props.onRemoveTask}>
                          <button
                            class="text-sm text-red-600 hover:text-red-700"
                            onClick={() => props.onRemoveTask?.(task.id!)}
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

          <Show when={props.error}>
            <div class="text-sm text-red-600">{props.error}</div>
          </Show>
        </div>
      </div>

      <Show when={isModalOpen()}>
        <div class="fixed inset-0 z-40">
          <button
            type="button"
            class="absolute inset-0 bg-black/40"
            onClick={handleCloseModal}
            aria-label="Close task configurator"
          />
          <div class="relative z-50 flex min-h-screen items-center justify-center px-4 py-8">
            <div class="w-full max-w-3xl rounded-2xl border border-amber-100/80 bg-white/95 shadow-xl">
              <div class="flex items-center justify-between border-b border-amber-100/80 px-6 py-4">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Task configurator
                  </div>
                  <div class="text-lg font-semibold text-stone-800">
                    {props.selectedAction?.() === "edit"
                      ? "Edit task"
                      : "Add a task"}
                  </div>
                </div>
                <button
                  type="button"
                  class="rounded-full border border-stone-200 px-3 py-1 text-sm font-medium text-stone-500 hover:text-stone-700"
                  onClick={handleCloseModal}
                >
                  Close
                </button>
              </div>

              <div class="px-6 py-5 space-y-5">
                <Show when={isPickingTask() || !props.selectedAction?.()}>
                  <div class="space-y-4">
                    <div class="text-sm text-stone-500">
                      Choose a task definition to add to this routine.
                    </div>
                    <Show when={!showCreateTaskDef()}>
                      <button
                        type="button"
                        class="text-sm text-amber-700 hover:text-amber-800 flex items-center gap-1"
                        onClick={() => setShowCreateTaskDef(true)}
                        disabled={props.isLoading}
                      >
                        <Icon key="plus" class="w-4 h-4" />
                        Create new task definition
                      </button>
                    </Show>

                    <Show when={showCreateTaskDef()}>
                      <div class="rounded-xl border border-amber-100/80 bg-amber-50/40 p-4 space-y-3">
                        <div class="flex items-center justify-between">
                          <div class="text-sm font-medium text-neutral-900">
                            Create task definition
                          </div>
                          <button
                            type="button"
                            class="text-xs text-neutral-500 hover:text-neutral-700"
                            onClick={() => {
                              setShowCreateTaskDef(false);
                              setNewTaskDefName("");
                              setNewTaskDefDescription("");
                              setNewTaskDefType("CHORE");
                            }}
                          >
                            Cancel
                          </button>
                        </div>

                        <Input
                          id="new_task_def_name"
                          placeholder="Task name"
                          value={newTaskDefName}
                          onChange={setNewTaskDefName}
                          required
                        />

                        <TextArea
                          id="new_task_def_description"
                          placeholder="Description"
                          value={newTaskDefDescription}
                          onChange={setNewTaskDefDescription}
                          rows={2}
                          required
                        />

                        <Select
                          id="new_task_def_type"
                          placeholder="Task Type"
                          value={newTaskDefType}
                          onChange={(val) => setNewTaskDefType(val as TaskType)}
                          options={ALL_TASK_TYPES}
                          required
                        />

                        <div class="flex gap-2">
                          <Button
                            type="button"
                            disabled={
                              isCreatingTaskDef() ||
                              !newTaskDefName().trim() ||
                              !newTaskDefDescription().trim()
                            }
                            onClick={() => void handleCreateTaskDefinition()}
                          >
                            {isCreatingTaskDef() ? "Creating..." : "Create & Add"}
                          </Button>
                        </div>
                      </div>
                    </Show>

                    <Show when={!showCreateTaskDef()}>
                      <Show
                        when={availableDefinitions().length > 0}
                        fallback={
                          <div class="text-sm text-neutral-500">
                            No task definitions available.
                          </div>
                        }
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
                    </Show>
                  </div>
                </Show>

                <Show
                  when={
                    props.selectedAction?.() &&
                    props.onTaskSubmit &&
                    props.onTaskCancel
                  }
                >
                  <div class="space-y-4">
                    <div>
                      <div class="text-sm font-medium text-neutral-900">
                        {props.selectedAction?.() === "add"
                          ? "Configure task"
                          : "Update task"}
                      </div>
                      <div class="text-xs text-neutral-500">
                        {getTaskDefinitionName(props.selectedTaskDefinitionId?.() ?? "")}
                      </div>
                    </div>

                    <Show when={props.setTaskName && props.taskName}>
                      <Input
                        id="routine_task_name"
                        placeholder="Task name (optional)"
                        value={props.taskName!}
                        onChange={props.setTaskName!}
                      />
                    </Show>

                    <div>
                      <label class="text-sm font-medium text-neutral-700 mb-2 block">
                        Time Schedule (when during the day)
                      </label>
                      <TaskScheduleForm
                        initialSchedule={props.scheduleInitial?.() ?? undefined}
                        onChange={(schedule: TaskSchedule) => {
                          setCurrentSchedule(schedule);
                        }}
                        onSubmit={() => Promise.resolve()}
                        onCancel={() => {}}
                        isLoading={false}
                        submitText=""
                      />
                    </div>

                    <div>
                      <label class="text-sm font-medium text-neutral-700 mb-2 block">
                        Recurrence Schedule (which days)
                      </label>
                      <RoutineScheduleForm
                        schedule={props.taskScheduleInitial?.() ?? null}
                        onScheduleChange={(schedule: RecurrenceSchedule | null) => {
                          setCurrentTaskSchedule(schedule);
                        }}
                        showOptionalToggle={true}
                        label="Task appears on specific days"
                      />
                    </div>

                    <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
                      <Button
                        type="button"
                        disabled={props.isLoading}
                        onClick={handleTaskSubmit}
                      >
                        {props.isLoading
                          ? "Saving..."
                          : props.selectedAction?.() === "add"
                          ? "Attach task"
                          : "Save changes"}
                      </Button>
                      <button
                        type="button"
                        class="px-4 py-2 text-sm font-medium text-neutral-700 bg-white border border-neutral-300 rounded-md hover:bg-neutral-50"
                        onClick={handleCloseModal}
                        disabled={props.isLoading}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </Show>

                <Show when={props.error}>
                  <div class="text-sm text-red-600">{props.error}</div>
                </Show>
              </div>
            </div>
          </div>
        </div>
      </Show>
    </div>
  );
};

export default RoutinePreview;
