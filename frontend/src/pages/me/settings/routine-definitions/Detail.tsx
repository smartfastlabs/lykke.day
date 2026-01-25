import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createMemo, createResource, createSignal } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import RoutineForm from "@/components/routine-definitions/Form";
import RoutinePreview from "@/components/routine-definitions/Preview";
import { routineDefinitionAPI, taskDefinitionAPI } from "@/utils/api";
import { globalLoading } from "@/providers/loading";
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
  const [isDirty, setIsDirty] = createSignal(false);

  const normalizeTimeWindow = (window: TimeWindow | null | undefined) => {
    if (!window) return null;
    const normalized: TimeWindow = {
      available_time: window.available_time || null,
      start_time: window.start_time || null,
      end_time: window.end_time || null,
      cutoff_time: window.cutoff_time || null,
    };
    return Object.values(normalized).some((value) => value) ? normalized : null;
  };

  const serializeRoutineDefinition = (value: Partial<RoutineDefinition>) =>
    JSON.stringify({
      name: (value.name ?? "").trim(),
      description: (value.description ?? "").trim(),
      category: value.category ?? "HYGIENE",
      routine_definition_schedule: value.routine_definition_schedule ?? {
        frequency: "DAILY",
        weekdays: null,
        day_number: null,
      },
      time_window: normalizeTimeWindow(value.time_window ?? null),
    });

  const initialSignature = createMemo(() => {
    const current = routineDefinition();
    if (!current) return null;
    return serializeRoutineDefinition(current);
  });

  const handleFormChange = (value: Partial<RoutineDefinition>) => {
    const baseline = initialSignature();
    if (!baseline) return;
    setIsDirty(serializeRoutineDefinition(value) !== baseline);
  };

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
    const stopLoading = globalLoading.start();
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
      stopLoading();
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
    const stopLoading = globalLoading.start();
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
      stopLoading();
      setIsTaskLoading(false);
    }
  };

  const handleCreateTaskDefinition = async (taskDef: TaskDefinition) => {
    setActionError("");
    const stopLoading = globalLoading.start();
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
    } finally {
      stopLoading();
    }
  };

  return (
    <Show
      when={routineDefinition()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <SettingsPage
          heading="Edit Routine"
          bottomLink={{
            label: "Back to Routine Definitions",
            url: "/me/settings/routine-definitions",
          }}
        >
          <div class="space-y-6">
            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Routine
                  </div>
                  <div class="text-lg font-semibold text-stone-800">
                    {current().name}
                  </div>
                  <Show
                    when={isDirty()}
                    fallback={
                      <div class="text-xs text-stone-400">
                        All changes saved
                      </div>
                    }
                  >
                    <div class="inline-flex items-center gap-2 text-xs font-medium text-amber-700">
                      <span class="h-2 w-2 rounded-full bg-amber-500" />
                      Unsaved changes
                    </div>
                  </Show>
                </div>
                <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <button
                    type="submit"
                    form="routine-definition-form"
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full bg-stone-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isLoading() ? "Saving..." : "Save changes"}
                  </button>
                  <button
                    type="button"
                    onClick={handleDelete}
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full border border-stone-200 bg-white px-5 py-3 text-sm font-semibold text-stone-600 shadow-sm transition hover:border-stone-300 hover:text-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Delete routine
                  </button>
                </div>
              </div>
            </div>

            <div class="grid gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
              <RoutineForm
                formId="routine-definition-form"
                initialData={current()}
                onSubmit={handleUpdate}
                onChange={handleFormChange}
                isLoading={isLoading()}
                error={error()}
                showSubmitButton={false}
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
                showBasicInfo={false}
                layout="embedded"
              />
            </div>
          </div>
        </SettingsPage>
      )}
    </Show>
  );
};

export default RoutineDefinitionDetailPage;
