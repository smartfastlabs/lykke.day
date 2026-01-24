import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import DetailPage from "@/components/shared/DetailPage";
import RoutineForm from "@/components/routines/Form";
import RoutinePreview from "@/components/routines/Preview";
import { routineDefinitionAPI, taskDefinitionAPI } from "@/utils/api";
import {
  RecurrenceSchedule,
  RoutineDefinition,
  RoutineDefinitionTask,
  TaskDefinition,
  TaskSchedule,
  TimeWindow,
} from "@/types/api";

const RoutineDefinitionDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [actionError, setActionError] = createSignal("");

  const [routineDefinition, { mutate: mutateRoutineDefinition }] =
    createResource<RoutineDefinition | undefined, string>(
    () => params.id,
    async (id) => {
      console.log("LOADING ROUTINE DEFINITION", id);
      return await routineDefinitionAPI.get(id);
    }
  );

  const [taskDefinitions, { refetch: refetchTaskDefinitions }] = createResource<TaskDefinition[]>(taskDefinitionAPI.getAll);

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
  const [isTaskLoading, setIsTaskLoading] = createSignal(false);

  const handleUpdate = async (
    partialRoutineDefinition: Partial<RoutineDefinition>
  ) => {
    const current = routineDefinition();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await routineDefinitionAPI.update({
        ...current,
        ...partialRoutineDefinition,
        id: current.id,
      });
      navigate("/me/settings/routine-definitions");
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to update routine definition";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = routineDefinition();
    if (!current || !current.id) return;
    setError("");
    setIsLoading(true);
    try {
      await routineDefinitionAPI.delete(current.id);
      navigate("/me/settings/routine-definitions");
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to delete routine definition";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

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
    setSelectedTaskDefinitionId(taskDef.id!);
    setSelectedAction("add");
    setTaskName(taskDef.name);
    setScheduleInitial(null);
    setTaskScheduleInitial(null);
    setTimeWindowInitial(null);
    setActionError("");
  };

  const openEditTask = (task: RoutineDefinitionTask) => {
    setSelectedTaskDefinitionId(task.task_definition_id);
    setSelectedRoutineDefinitionTaskId(task.id!);
    setSelectedAction("edit");
    setTaskName(task.name ?? "");
    setScheduleInitial(task.schedule ?? null);
    setTaskScheduleInitial(task.task_schedule ?? null);
    setTimeWindowInitial(task.time_window ?? null);
    setActionError("");
  };

  const handleTaskSubmit = async (
    schedule: TaskSchedule,
    taskSchedule: RecurrenceSchedule | null,
    timeWindow: TimeWindow | null
  ) => {
    const current = routineDefinition();
    const action = selectedAction();
    const taskDefinitionId = selectedTaskDefinitionId();
    const routineDefinitionTaskId = selectedRoutineDefinitionTaskId();
    if (!current || !current.id || !action || !taskDefinitionId) return;

    setIsTaskLoading(true);
    setActionError("");
    try {
      const nameValue = taskName().trim() || null;
      let updated: RoutineDefinition;

      if (action === "add") {
        updated = await routineDefinitionAPI.addTask(current.id, {
          task_definition_id: taskDefinitionId,
          name: nameValue ?? undefined,
          schedule,
          task_schedule: taskSchedule ?? undefined,
          time_window: timeWindow ?? undefined,
        });
      } else {
        if (!routineDefinitionTaskId) {
          setActionError("Routine definition task ID is required for update");
          return;
        }
        updated = await routineDefinitionAPI.updateTask(
          current.id,
          routineDefinitionTaskId,
          {
          name: nameValue ?? undefined,
          schedule,
          task_schedule: taskSchedule ?? undefined,
          time_window: timeWindow ?? undefined,
          }
        );
      }

      mutateRoutineDefinition(updated);
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

  const handleRemoveTask = async (
    routineDefinitionTaskId: string
  ) => {
    const current = routineDefinition();
    if (!current?.id) return;

    setIsTaskLoading(true);
    setActionError("");
    try {
      const updated = await routineDefinitionAPI.removeTask(
        current.id,
        routineDefinitionTaskId
      );
      mutateRoutineDefinition(updated);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to remove task";
      setActionError(message);
    } finally {
      setIsTaskLoading(false);
    }
  };

  const handleCreateTaskDefinition = async (taskDef: TaskDefinition) => {
    setActionError("");
    try {
      const current = routineDefinition();
      if (!current?.user_id) {
        setActionError("Unable to determine user for task definition");
        return;
      }
      // Create the task definition
      const created = await taskDefinitionAPI.create({
        name: taskDef.name,
        description: taskDef.description,
        type: taskDef.type,
        user_id: current.user_id,
      });
      
      // Refresh the task definitions list
      await refetchTaskDefinitions();
      
      // Automatically select it and open the add task form
      openAddTask(created);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to create task definition";
      setActionError(message);
      throw err;
    }
  };

  return (
    <Show
      when={routineDefinition()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <DetailPage
          heading="Routine Definition"
          bottomLink={{
            label: "Back to Routine Definitions",
            url: "/me/settings/routine-definitions",
          }}
          preview={
            <RoutinePreview
              routineDefinition={current()}
              taskDefinitions={taskDefinitions()}
              isEditMode={false}
            />
          }
          edit={
            <div class="flex flex-col items-center justify-center px-6 py-8">
              <div class="w-full max-w-3xl space-y-8">
                <RoutineForm
                  initialData={current()}
                  onSubmit={handleUpdate}
                  isLoading={isLoading()}
                  error={error()}
                />
                <RoutinePreview
                  routineDefinition={current()}
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
                />
              </div>
            </div>
          }
          onDelete={handleDelete}
        />
      )}
    </Show>
  );
};

export default RoutineDefinitionDetailPage;
