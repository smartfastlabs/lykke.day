import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import DetailPage from "@/components/shared/detailPage";
import RoutineForm from "@/components/routines/form";
import RoutinePreview from "@/components/routines/preview";
import { routineAPI, taskDefinitionAPI } from "@/utils/api";
import { Routine, RoutineTask, TaskDefinition, TaskSchedule } from "@/types/api";

const RoutineDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [actionError, setActionError] = createSignal("");

  const [routine, { mutate: mutateRoutine }] = createResource<Routine | undefined, string>(
    () => params.id,
    async (id) => {
      console.log("LOADING ROUTINE", id);
      return await routineAPI.get(id);
    }
  );

  const [taskDefinitions] = createResource<TaskDefinition[]>(taskDefinitionAPI.getAll);

  const [selectedTaskDefinitionId, setSelectedTaskDefinitionId] = createSignal<string | null>(
    null
  );
  const [selectedRoutineTaskId, setSelectedRoutineTaskId] = createSignal<string | null>(null);
  const [selectedAction, setSelectedAction] = createSignal<"add" | "edit" | null>(null);
  const [taskName, setTaskName] = createSignal("");
  const [scheduleInitial, setScheduleInitial] = createSignal<TaskSchedule | null>(null);
  const [isTaskLoading, setIsTaskLoading] = createSignal(false);

  const handleUpdate = async (partialRoutine: Partial<Routine>) => {
    const current = routine();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await routineAPI.update({
        ...current,
        ...partialRoutine,
        id: current.id,
      });
      navigate("/settings/routines");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update routine";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = routine();
    if (!current || !current.id) return;
    setError("");
    setIsLoading(true);
    try {
      await routineAPI.delete(current.id);
      navigate("/settings/routines");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete routine";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const resetTaskForm = () => {
    setSelectedTaskDefinitionId(null);
    setSelectedRoutineTaskId(null);
    setSelectedAction(null);
    setScheduleInitial(null);
    setTaskName("");
    setActionError("");
  };

  const openAddTask = (taskDef: TaskDefinition) => {
    setSelectedTaskDefinitionId(taskDef.id!);
    setSelectedAction("add");
    setTaskName(taskDef.name);
    setScheduleInitial(null);
    setActionError("");
  };

  const openEditTask = (task: RoutineTask) => {
    setSelectedTaskDefinitionId(task.task_definition_id);
    setSelectedRoutineTaskId(task.id!);
    setSelectedAction("edit");
    setTaskName(task.name ?? "");
    setScheduleInitial(task.schedule ?? null);
    setActionError("");
  };

  const handleTaskSubmit = async (schedule: TaskSchedule) => {
    const current = routine();
    const action = selectedAction();
    const taskDefinitionId = selectedTaskDefinitionId();
    const routineTaskId = selectedRoutineTaskId();
    if (!current || !current.id || !action || !taskDefinitionId) return;

    setIsTaskLoading(true);
    setActionError("");
    try {
      const nameValue = taskName().trim() || null;
      let updated: Routine;

      if (action === "add") {
        updated = await routineAPI.addTask(current.id, {
          task_definition_id: taskDefinitionId,
          name: nameValue ?? undefined,
          schedule,
        });
      } else {
        if (!routineTaskId) {
          setActionError("Routine task ID is required for update");
          return;
        }
        updated = await routineAPI.updateTask(current.id, routineTaskId, {
          name: nameValue ?? undefined,
          schedule,
        });
      }

      mutateRoutine(updated);
      resetTaskForm();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save routine task";
      setActionError(message);
    } finally {
      setIsTaskLoading(false);
    }
  };

  const handleRemoveTask = async (routineTaskId: string) => {
    const current = routine();
    if (!current?.id) return;

    setIsTaskLoading(true);
    setActionError("");
    try {
      const updated = await routineAPI.removeTask(current.id, routineTaskId);
      mutateRoutine(updated);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to remove task";
      setActionError(message);
    } finally {
      setIsTaskLoading(false);
    }
  };

  return (
    <Show
      when={routine()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <DetailPage
          heading="Routine"
          bottomLink={{ label: "Back to Routines", url: "/settings/routines" }}
          preview={
            <RoutinePreview
              routine={current()}
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
                  routine={current()}
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

export default RoutineDetailPage;
