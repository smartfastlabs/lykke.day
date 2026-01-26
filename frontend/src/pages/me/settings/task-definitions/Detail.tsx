import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createMemo, createResource, createSignal } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import TaskDefinitionForm from "@/components/task-definitions/Form";
import { taskDefinitionAPI } from "@/utils/api";
import { TaskDefinition } from "@/types/api";

const TaskDefinitionDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [isDirty, setIsDirty] = createSignal(false);

  const [taskDefinition] = createResource<TaskDefinition | undefined, string>(
    () => params.id,
    async (id) => taskDefinitionAPI.get(id)
  );

  const serializeTaskDefinition = (value: Partial<TaskDefinition>) =>
    JSON.stringify({
      name: (value.name ?? "").trim(),
      description: (value.description ?? "").trim(),
      type: value.type ?? "CHORE",
    });

  const initialSignature = createMemo(() => {
    const current = taskDefinition();
    if (!current) return null;
    return serializeTaskDefinition(current);
  });

  const handleFormChange = (value: Partial<TaskDefinition>) => {
    const baseline = initialSignature();
    if (!baseline) return;
    setIsDirty(serializeTaskDefinition(value) !== baseline);
  };

  const handleUpdate = async (
    partialTaskDefinition: Partial<TaskDefinition>
  ) => {
    const current = taskDefinition();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await taskDefinitionAPI.update({
        ...current,
        ...partialTaskDefinition,
        id: current.id,
      });
      navigate("/me/settings/task-definitions");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update task definition";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = taskDefinition();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await taskDefinitionAPI.delete(current.id);
      navigate("/me/settings/task-definitions");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete task definition";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Show
      when={taskDefinition()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <SettingsPage
          heading="Edit Task Definition"
          bottomLink={{
            label: "Back to Task Definitions",
            url: "/me/settings/task-definitions",
          }}
        >
          <div class="space-y-6">
            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Task Definition
                  </div>
                  <div class="text-lg font-semibold text-stone-800">
                    {current().name}
                  </div>
                  <Show
                    when={isDirty()}
                    fallback={<div class="text-xs text-stone-400">All changes saved</div>}
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
                    form="task-definition-form"
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
                    Delete task definition
                  </button>
                </div>
              </div>
            </div>

            <TaskDefinitionForm
              formId="task-definition-form"
              initialData={current()}
              onSubmit={handleUpdate}
              onChange={handleFormChange}
              isLoading={isLoading()}
              error={error()}
              showSubmitButton={false}
            />
          </div>
        </SettingsPage>
      )}
    </Show>
  );
};

export default TaskDefinitionDetailPage;

