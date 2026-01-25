import { Show, createMemo, createResource, createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import SettingsPage from "@/components/shared/SettingsPage";
import RoutinePreview from "@/components/routine-definitions/Preview";
import RoutineForm from "@/components/routine-definitions/Form";
import { routineDefinitionAPI, taskDefinitionAPI } from "@/utils/api";
import {
  RecurrenceSchedule,
  RoutineDefinition,
  RoutineDefinitionTask,
  TaskDefinition,
  TaskSchedule,
  TimeWindow,
} from "@/types/api";

export default function NewRoutineDefinition() {
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [actionError, setActionError] = createSignal("");
  const [isTaskLoading, setIsTaskLoading] = createSignal(false);

  const [tasks, setTasks] = createSignal<RoutineDefinitionTask[]>([]);
  const [draft, setDraft] = createSignal<Partial<RoutineDefinition>>({
    name: "",
    description: "",
    category: "HYGIENE",
    routine_definition_schedule: {
      frequency: "DAILY",
      weekdays: null,
      day_number: null,
    },
  });

  const [taskDefinitions, { refetch: refetchTaskDefinitions }] = createResource<TaskDefinition[]>(
    taskDefinitionAPI.getAll
  );
  const [selectedTaskDefinitionId, setSelectedTaskDefinitionId] = createSignal<string | null>(
    null
  );
  const [selectedRoutineDefinitionTaskId, setSelectedRoutineDefinitionTaskId] =
    createSignal<string | null>(null);
  const [selectedAction, setSelectedAction] = createSignal<"add" | "edit" | null>(null);
  const [taskName, setTaskName] = createSignal("");
  const [scheduleInitial, setScheduleInitial] = createSignal<TaskSchedule | null>(null);
  const [taskScheduleInitial, setTaskScheduleInitial] = createSignal<RecurrenceSchedule | null>(null);
  const [timeWindowInitial, setTimeWindowInitial] = createSignal<TimeWindow | null>(null);

  const handleSubmit = async (
    routineDefinition: Partial<RoutineDefinition>
  ) => {
    setError("");
    setIsLoading(true);

    try {
      await routineDefinitionAPI.create(
        {
          ...routineDefinition,
          tasks: tasks(),
        } as RoutineDefinition
      );
      navigate("/me/settings/routine-definitions");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to create routine definition";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const routineDefinitionPreview = createMemo<RoutineDefinition>(() => ({
    id: undefined,
    user_id: "",
    name: draft().name ?? "",
    description: draft().description ?? "",
    category: draft().category ?? "HYGIENE",
    routine_definition_schedule:
      draft().routine_definition_schedule ?? {
      frequency: "DAILY",
      weekdays: null,
      day_number: null,
    },
    tasks: tasks(),
  }));

  const resetTaskForm = () => {
    setSelectedTaskDefinitionId(null);
    setSelectedRoutineDefinitionTaskId(null);
    setSelectedAction(null);
    setScheduleInitial(null);
    setTaskScheduleInitial(null);
    setTimeWindowInitial(null);
    setTaskName("");
    setActionError("");
  };

  const openAddTask = (taskDef: TaskDefinition) => {
    if (!taskDef.id) return;
    setSelectedTaskDefinitionId(taskDef.id);
    setSelectedAction("add");
    setTaskName(taskDef.name);
    setScheduleInitial(null);
    setTaskScheduleInitial(null);
    setTimeWindowInitial(null);
    setActionError("");
  };

  const openEditTask = (task: RoutineDefinitionTask) => {
    if (!task.id) return;
    setSelectedTaskDefinitionId(task.task_definition_id);
    setSelectedRoutineDefinitionTaskId(task.id);
    setSelectedAction("edit");
    setTaskName(task.name ?? "");
    setScheduleInitial(task.schedule ?? null);
    setTaskScheduleInitial(task.task_schedule ?? null);
    setTimeWindowInitial(task.time_window ?? null);
    setActionError("");
  };

  const handleRemoveTask = (routineDefinitionTaskId: string) => {
    setTasks((prev) =>
      prev.filter((task) => task.id !== routineDefinitionTaskId)
    );
  };

  const handleCreateTaskDefinition = async (taskDef: TaskDefinition) => {
    setActionError("");
    try {
      const created = await taskDefinitionAPI.create({
        name: taskDef.name,
        description: taskDef.description,
        type: taskDef.type,
      });

      await refetchTaskDefinitions();

      openAddTask(created);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to create task definition";
      setActionError(message);
      throw err;
    }
  };

  const generateTaskId = () =>
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2);

  const handleTaskSubmit = async (
    schedule: TaskSchedule,
    taskSchedule: RecurrenceSchedule | null,
    timeWindow: TimeWindow | null
  ) => {
    const action = selectedAction();
    const taskDefinitionId = selectedTaskDefinitionId();
    const routineDefinitionTaskId = selectedRoutineDefinitionTaskId();
    if (!action || !taskDefinitionId) return;

    setIsTaskLoading(true);
    setActionError("");

    try {
      const nameValue = taskName().trim() || null;

      if (action === "add") {
        const newTask: RoutineDefinitionTask = {
          id: generateTaskId(),
          task_definition_id: taskDefinitionId,
          name: nameValue ?? undefined,
          schedule,
          task_schedule: taskSchedule ?? undefined,
          time_window: timeWindow ?? undefined,
        };
        setTasks((prev) => [...prev, newTask]);
      } else {
        if (!routineDefinitionTaskId) {
          setActionError("Routine definition task ID is required for update");
          return;
        }
        setTasks((prev) =>
          prev.map((task) =>
            task.id === routineDefinitionTaskId
              ? {
                  ...task,
                  name: nameValue ?? undefined,
                  schedule,
                  task_schedule: taskSchedule ?? undefined,
                  time_window: timeWindow ?? undefined,
                }
              : task
          )
        );
      }

      resetTaskForm();
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to save routine definition task";
      setActionError(message);
    } finally {
      setIsTaskLoading(false);
    }
  };

  return (
    <SettingsPage
      heading="Create Routine Definition"
      bottomLink={{
        label: "Back to Routine Definitions",
        url: "/me/settings/routine-definitions",
      }}
    >
      <div class="flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-5xl space-y-8">
          <div class="w-full max-w-xl">
            <RoutineForm
              onSubmit={handleSubmit}
              onChange={setDraft}
              isLoading={isLoading()}
              error={error()}
              tasks={tasks()}
              beforeSubmit={
                <Show when={routineDefinitionPreview()}>
                  <RoutinePreview
                    routineDefinition={routineDefinitionPreview()}
                    taskDefinitions={taskDefinitions()}
                    onAddTask={openAddTask}
                    onCreateTaskDefinition={handleCreateTaskDefinition}
                    onEditTask={openEditTask}
                    onRemoveTask={handleRemoveTask}
                    onTaskSubmit={handleTaskSubmit}
                    onTaskCancel={resetTaskForm}
                    selectedTaskDefinitionId={selectedTaskDefinitionId}
                    selectedAction={selectedAction}
                    taskName={taskName}
                    setTaskName={setTaskName}
                    scheduleInitial={scheduleInitial}
                    taskScheduleInitial={taskScheduleInitial}
                    timeWindowInitial={timeWindowInitial}
                    isEditMode={true}
                    isLoading={isTaskLoading()}
                    error={actionError()}
                    showBasicInfo={false}
                  />
                </Show>
              }
            />
          </div>
        </div>
      </div>
    </SettingsPage>
  );
}
