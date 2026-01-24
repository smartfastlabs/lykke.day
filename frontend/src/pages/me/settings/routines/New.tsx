import { Show, createMemo, createResource, createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import SettingsPage from "@/components/shared/SettingsPage";
import RoutinePreview from "@/components/routines/Preview";
import RoutineForm from "@/components/routines/Form";
import { routineAPI, taskDefinitionAPI } from "@/utils/api";
import { Routine, RoutineTask, TaskDefinition, TaskSchedule, TimeWindow, RecurrenceSchedule } from "@/types/api";

export default function NewRoutine() {
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [actionError, setActionError] = createSignal("");
  const [isTaskLoading, setIsTaskLoading] = createSignal(false);

  const [tasks, setTasks] = createSignal<RoutineTask[]>([]);
  const [draft, setDraft] = createSignal<Partial<Routine>>({
    name: "",
    description: "",
    category: "HYGIENE",
    routine_schedule: {
      frequency: "DAILY",
      weekdays: null,
      day_number: null,
    },
  });

  const [taskDefinitions] = createResource<TaskDefinition[]>(taskDefinitionAPI.getAll);
  const [selectedTaskDefinitionId, setSelectedTaskDefinitionId] = createSignal<string | null>(
    null
  );
  const [selectedRoutineTaskId, setSelectedRoutineTaskId] = createSignal<string | null>(null);
  const [selectedAction, setSelectedAction] = createSignal<"add" | "edit" | null>(null);
  const [taskName, setTaskName] = createSignal("");
  const [scheduleInitial, setScheduleInitial] = createSignal<TaskSchedule | null>(null);
  const [taskScheduleInitial, setTaskScheduleInitial] = createSignal<RecurrenceSchedule | null>(null);
  const [timeWindowInitial, setTimeWindowInitial] = createSignal<TimeWindow | null>(null);

  const handleSubmit = async (routine: Partial<Routine>) => {
    setError("");
    setIsLoading(true);

    try {
      await routineAPI.create(
        {
          ...routine,
          tasks: tasks(),
        } as Routine
      );
      navigate("/me/settings/routines");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create routine";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const routinePreview = createMemo<Routine>(() => ({
    id: undefined,
    user_id: "",
    name: draft().name ?? "",
    description: draft().description ?? "",
    category: draft().category ?? "HYGIENE",
    routine_schedule: draft().routine_schedule ?? {
      frequency: "DAILY",
      weekdays: null,
      day_number: null,
    },
    tasks: tasks(),
  }));

  const resetTaskForm = () => {
    setSelectedTaskDefinitionId(null);
    setSelectedRoutineTaskId(null);
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

  const openEditTask = (task: RoutineTask) => {
    if (!task.id) return;
    setSelectedTaskDefinitionId(task.task_definition_id);
    setSelectedRoutineTaskId(task.id);
    setSelectedAction("edit");
    setTaskName(task.name ?? "");
    setScheduleInitial(task.schedule ?? null);
    setTaskScheduleInitial(task.task_schedule ?? null);
    setTimeWindowInitial(task.time_window ?? null);
    setActionError("");
  };

  const handleRemoveTask = (routineTaskId: string) => {
    setTasks((prev) => prev.filter((task) => task.id !== routineTaskId));
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
    const routineTaskId = selectedRoutineTaskId();
    if (!action || !taskDefinitionId) return;

    setIsTaskLoading(true);
    setActionError("");

    try {
      const nameValue = taskName().trim() || null;

      if (action === "add") {
        const newTask: RoutineTask = {
          id: generateTaskId(),
          task_definition_id: taskDefinitionId,
          name: nameValue ?? undefined,
          schedule,
          task_schedule: taskSchedule ?? undefined,
          time_window: timeWindow ?? undefined,
        };
        setTasks((prev) => [...prev, newTask]);
      } else {
        if (!routineTaskId) {
          setActionError("Routine task ID is required for update");
          return;
        }
        setTasks((prev) =>
          prev.map((task) =>
            task.id === routineTaskId
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
      const message = err instanceof Error ? err.message : "Failed to save routine task";
      setActionError(message);
    } finally {
      setIsTaskLoading(false);
    }
  };

  return (
    <SettingsPage
      heading="Create Routine"
      bottomLink={{ label: "Back to Routines", url: "/me/settings/routines" }}
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
                <Show when={routinePreview()}>
                  <RoutinePreview
                    routine={routinePreview()}
                    taskDefinitions={taskDefinitions()}
                    onAddTask={openAddTask}
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
