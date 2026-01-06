import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import DetailPage from "@/components/shared/detailPage";
import TaskDefinitionForm from "@/components/taskDefinitions/form";
import TaskDefinitionPreview from "@/components/taskDefinitions/preview";
import { taskDefinitionAPI } from "@/utils/api";
import { TaskDefinition } from "@/types/api";

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
    <Show
      when={taskDefinition()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <DetailPage
          heading="Task Definition"
          bottomLink={{ label: "Back to Task Definitions", url: "/settings/task-definitions" }}
          preview={<TaskDefinitionPreview taskDefinition={current()} />}
          edit={
            <div class="flex flex-col items-center justify-center px-6 py-8">
              <div class="w-full max-w-sm space-y-6">
                <TaskDefinitionForm
                  initialData={current()}
                  onSubmit={handleUpdate}
                  isLoading={isLoading()}
                  error={error()}
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

export default TaskDefinitionDetailPage;

