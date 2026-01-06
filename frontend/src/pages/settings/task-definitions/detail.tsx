import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import Page from "../../../components/shared/layout/page";
import TaskDefinitionForm from "../../../components/taskDefinitions/form";
import { taskDefinitionAPI } from "../../../utils/api";
import { TaskDefinition } from "../../../types/api";

const TaskDefinitionDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const [taskDefinition] = createResource<TaskDefinition | undefined, string>(
    () => params.id,
    async (id) => taskDefinitionAPI.get(id)
  );

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
      navigate("/settings/task-definitions");
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
      navigate("/settings/task-definitions");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete task definition";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Page>
      <Show
        when={taskDefinition()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        {(current) => (
          <div class="min-h-screen bg-neutral-50 flex flex-col items-center justify-center px-6">
            <div class="w-full max-w-sm space-y-6">
              <div class="flex items-center justify-between">
                <h1 class="text-2xl font-medium text-neutral-900">
                  Edit Task Definition
                </h1>
                <button
                  type="button"
                  class="text-sm text-red-600 hover:text-red-700"
                  onClick={handleDelete}
                  disabled={isLoading()}
                >
                  Delete
                </button>
              </div>

              <TaskDefinitionForm
                initialData={current()}
                onSubmit={handleUpdate}
                isLoading={isLoading()}
                error={error()}
              />
            </div>
          </div>
        )}
      </Show>
    </Page>
  );
};

export default TaskDefinitionDetailPage;

