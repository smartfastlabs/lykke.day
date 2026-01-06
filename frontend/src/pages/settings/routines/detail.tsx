import { useNavigate, useParams } from "@solidjs/router";
import { Component, For, Show, createMemo, createResource, createSignal } from "solid-js";
import SettingsPage, { ActionButton } from "@/components/shared/settingsPage";
import RoutineForm from "@/components/routines/form";
import TaskScheduleForm from "@/components/tasks/scheduleForm";
import { Icon } from "@/components/shared/icon";
import { routineAPI, taskDefinitionAPI } from "@/utils/api";
import { Routine, RoutineTask, TaskDefinition, TaskSchedule } from "@/types/api";
import { Input } from "@/components/forms";

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

  const [isEditMode, setIsEditMode] = createSignal(false);
  const [selectedTaskDefinitionId, setSelectedTaskDefinitionId] = createSignal<string | null>(
    null
  );
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
    setSelectedAction("edit");
    setTaskName(task.name ?? "");
    setScheduleInitial(task.schedule ?? null);
    setActionError("");
  };

  const handleTaskSubmit = async (schedule: TaskSchedule) => {
    const current = routine();
    const action = selectedAction();
    const taskDefinitionId = selectedTaskDefinitionId();
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
        updated = await routineAPI.updateTask(current.id, taskDefinitionId, {
          name: nameValue ?? undefined,
          schedule,
        });
      }

      mutateRoutine(updated);
      resetTaskForm();
      setIsEditMode(true);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save routine task";
      setActionError(message);
    } finally {
      setIsTaskLoading(false);
    }
  };

  const handleRemoveTask = async (taskDefinitionId: string) => {
    const current = routine();
    if (!current?.id) return;

    setIsTaskLoading(true);
    setActionError("");
    try {
      const updated = await routineAPI.removeTask(current.id, taskDefinitionId);
      mutateRoutine(updated);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to remove task";
      setActionError(message);
    } finally {
      setIsTaskLoading(false);
    }
  };

  const attachedTasks = createMemo(() => routine()?.tasks ?? []);

  const attachedTaskIds = createMemo(
    () => new Set(attachedTasks().map((task) => task.task_definition_id))
  );

  const availableDefinitions = createMemo(() =>
    (taskDefinitions() ?? []).filter((def) => !attachedTaskIds().has(def.id!))
  );

  const getTaskDefinitionName = (taskDefinitionId: string) =>
    taskDefinitions()?.find((def) => def.id === taskDefinitionId)?.name ?? taskDefinitionId;

  const actionButtons = createMemo((): ActionButton[] => {
    return [
      {
        label: isEditMode() ? "Exit Edit Mode" : "Edit Mode",
        onClick: () => setIsEditMode((prev) => !prev),
      },
      {
        label: "Delete",
        onClick: handleDelete,
      },
    ];
  });

  return (
    <SettingsPage
      heading="Edit Routine"
      actionButtons={actionButtons()}
      bottomLink={{ label: "Back to Routines", url: "/settings/routines" }}
    >
      <Show
        when={routine()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        {(current) => (
          <div class="flex flex-col items-center justify-center px-6 py-8">
            <div class="w-full max-w-3xl space-y-8">

              <RoutineForm
                initialData={current()}
                onSubmit={handleUpdate}
                isLoading={isLoading()}
                error={error()}
              />

              <div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-4">
                <div class="flex items-center justify-between">
                  <div>
                    <h2 class="text-lg font-medium text-neutral-900">Routine Tasks</h2>
                    <p class="text-sm text-neutral-500">
                      Manage tasks attached to this routine.
                    </p>
                  </div>
                  <Show when={isEditMode()}>
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
                                    task.schedule.start_time
                                      ? ` • ${task.schedule.start_time}`
                                      : ""
                                  }${
                                    task.schedule.end_time ? ` - ${task.schedule.end_time}` : ""
                                  }`
                                : "No schedule set"}
                            </div>
                          </div>
                          <Show when={isEditMode()}>
                            <div class="flex items-center gap-2">
                              <button
                                class="text-sm text-blue-600 hover:text-blue-700"
                                onClick={() => openEditTask(task)}
                                disabled={isTaskLoading()}
                              >
                                Edit
                              </button>
                              <button
                                class="text-sm text-red-600 hover:text-red-700"
                                onClick={() => handleRemoveTask(task.task_definition_id)}
                                disabled={isTaskLoading()}
                              >
                                Remove
                              </button>
                            </div>
                          </Show>
                        </div>
                      )}
                    </For>
                  </div>
                </Show>

                <Show when={isEditMode()}>
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
                              onClick={() => openAddTask(def)}
                              disabled={isTaskLoading()}
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

                <Show when={selectedAction()}>
                  <div class="mt-4 rounded-md border border-neutral-200 bg-neutral-50 p-4 space-y-3">
                    <div class="flex items-center justify-between">
                      <div>
                        <div class="text-sm font-medium text-neutral-900">
                          {selectedAction() === "add" ? "Add Task" : "Edit Task"}
                        </div>
                        <div class="text-xs text-neutral-500">
                          {getTaskDefinitionName(selectedTaskDefinitionId() ?? "")}
                        </div>
                      </div>
                      <button
                        type="button"
                        class="text-xs text-neutral-500 hover:text-neutral-700"
                        onClick={resetTaskForm}
                      >
                        Cancel
                      </button>
                    </div>

                    <Input
                      id="routine_task_name"
                      placeholder="Task name (optional)"
                      value={taskName}
                      onChange={setTaskName}
                    />

                    <TaskScheduleForm
                      initialSchedule={scheduleInitial()}
                      onSubmit={handleTaskSubmit}
                      onCancel={resetTaskForm}
                      isLoading={isTaskLoading()}
                      submitText={selectedAction() === "add" ? "Attach Task" : "Save"}
                    />

                    <Show when={actionError()}>
                      <div class="text-sm text-red-600">{actionError()}</div>
                    </Show>
                  </div>
                </Show>
              </div>
            </div>
          </div>
        )}
      </Show>
    </SettingsPage>
  );
};

export default RoutineDetailPage;
