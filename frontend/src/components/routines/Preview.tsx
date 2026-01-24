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
import RoutineScheduleForm from "@/components/routines/RoutineScheduleForm";
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
  const [timeWindowAvailable, setTimeWindowAvailable] = createSignal("");
  const [timeWindowStart, setTimeWindowStart] = createSignal("");
  const [timeWindowEnd, setTimeWindowEnd] = createSignal("");
  const [timeWindowCutoff, setTimeWindowCutoff] = createSignal("");
  
  // State for creating new task definition
  const [showCreateTaskDef, setShowCreateTaskDef] = createSignal(false);
  const [newTaskDefName, setNewTaskDefName] = createSignal("");
  const [newTaskDefDescription, setNewTaskDefDescription] = createSignal("");
  const [newTaskDefType, setNewTaskDefType] = createSignal<TaskType>("CHORE");
  const [isCreatingTaskDef, setIsCreatingTaskDef] = createSignal(false);
  
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
      const initialWindow = props.timeWindowInitial?.() ?? null;
      setTimeWindowAvailable(initialWindow?.available_time ?? "");
      setTimeWindowStart(initialWindow?.start_time ?? "");
      setTimeWindowEnd(initialWindow?.end_time ?? "");
      setTimeWindowCutoff(initialWindow?.cutoff_time ?? "");
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

  const buildTimeWindow = (): TimeWindow | null => {
    const timeWindow: TimeWindow = {
      available_time: timeWindowAvailable() || null,
      start_time: timeWindowStart() || null,
      end_time: timeWindowEnd() || null,
      cutoff_time: timeWindowCutoff() || null,
    };
    return Object.values(timeWindow).some((value) => value) ? timeWindow : null;
  };

  const handleTaskSubmit = () => {
    const schedule = currentSchedule() ?? {
      timing_type: "FLEXIBLE" as const,
      available_time: null,
      start_time: null,
      end_time: null,
    };
    const taskSchedule = currentTaskSchedule();
    const timeWindow = buildTimeWindow();
    void props.onTaskSubmit?.(schedule, taskSchedule, timeWindow);
  };

  const getTaskDefinitionName = (taskDefinitionId: string) =>
    props.taskDefinitions?.find((def) => def.id === taskDefinitionId)?.name ?? taskDefinitionId;

  return (
    <div class="flex flex-col items-center justify-center px-0 py-8">
      <div class="w-full max-w-3xl space-y-8">
        <Show when={props.showBasicInfo ?? true}>
          <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
            <h2 class="text-lg font-medium text-neutral-900">Basic Information</h2>
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
        <div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-medium text-neutral-900">
                Routine Definition Tasks
              </h2>
              <p class="text-sm text-neutral-500">
                Tasks attached to this routine definition.
              </p>
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
                        {task.time_window && (
                          <div>
                            Window:
                            {task.time_window.available_time
                              ? ` ${task.time_window.available_time}`
                              : ""}
                            {task.time_window.start_time
                              ? ` • ${task.time_window.start_time}`
                              : ""}
                            {task.time_window.end_time ? ` - ${task.time_window.end_time}` : ""}
                            {task.time_window.cutoff_time
                              ? ` • Cutoff ${task.time_window.cutoff_time}`
                              : ""}
                          </div>
                        )}
                        {!task.schedule && !task.task_schedule && !task.time_window && (
                          <div>No schedule set</div>
                        )}
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

          <Show when={props.isEditMode && props.onAddTask}>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <div class="text-sm font-medium text-neutral-900">Add task</div>
                <Show when={!showCreateTaskDef()}>
                  <button
                    type="button"
                    class="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                    onClick={() => setShowCreateTaskDef(true)}
                    disabled={props.isLoading}
                  >
                    <Icon key="plus" class="w-4 h-4" />
                    Create New
                  </button>
                </Show>
              </div>
              
              <Show when={showCreateTaskDef()}>
                <div class="rounded-md border border-neutral-200 bg-neutral-50 p-4 space-y-3">
                  <div class="flex items-center justify-between">
                    <div class="text-sm font-medium text-neutral-900">Create Task Definition</div>
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
                      disabled={isCreatingTaskDef() || !newTaskDefName().trim() || !newTaskDefDescription().trim()}
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
                  fallback={<div class="text-sm text-neutral-500">No task definitions available.</div>}
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
                <div class="space-y-4">
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

                  <div>
                    <label class="text-sm font-medium text-neutral-700 mb-2 block">
                      Time Window (optional)
                    </label>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <div class="space-y-1">
                        <label class="text-xs font-medium text-neutral-600" for="time_window_available">
                          Preferred time
                        </label>
                        <Input
                          id="time_window_available"
                          type="time"
                          placeholder="Preferred time"
                          value={timeWindowAvailable}
                          onChange={setTimeWindowAvailable}
                        />
                      </div>
                      <div class="space-y-1">
                        <label class="text-xs font-medium text-neutral-600" for="time_window_start">
                          Start time
                        </label>
                        <Input
                          id="time_window_start"
                          type="time"
                          placeholder="Start time"
                          value={timeWindowStart}
                          onChange={setTimeWindowStart}
                        />
                      </div>
                      <div class="space-y-1">
                        <label class="text-xs font-medium text-neutral-600" for="time_window_end">
                          End time
                        </label>
                        <Input
                          id="time_window_end"
                          type="time"
                          placeholder="End time"
                          value={timeWindowEnd}
                          onChange={setTimeWindowEnd}
                        />
                      </div>
                      <div class="space-y-1">
                        <label class="text-xs font-medium text-neutral-600" for="time_window_cutoff">
                          Cutoff time
                        </label>
                        <Input
                          id="time_window_cutoff"
                          type="time"
                          placeholder="Cutoff time"
                          value={timeWindowCutoff}
                          onChange={setTimeWindowCutoff}
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div class="flex gap-2 pt-2">
                    <Button
                      type="button"
                      disabled={props.isLoading}
                      onClick={handleTaskSubmit}
                    >
                      {props.isLoading ? "Saving..." : (props.selectedAction?.() === "add" ? "Attach Task" : "Save")}
                    </Button>
                    <button
                      type="button"
                      class="px-4 py-2 text-sm font-medium text-neutral-700 bg-white border border-neutral-300 rounded-md hover:bg-neutral-50"
                      onClick={() => props.onTaskCancel?.()}
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
          </Show>
        </div>
      </div>
    </div>
  );
};

export default RoutinePreview;

