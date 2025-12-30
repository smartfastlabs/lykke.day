import { createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import Page from "../../../components/shared/layout/page";
import { taskDefinitionAPI } from "../../../utils/api";
import { TaskDefinition } from "../../../types/api";
import TaskDefinitionForm from "../../../components/taskDefinitions/form";

export default function NewTaskDefinition() {
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (taskDefinition: Partial<TaskDefinition>) => {
    setError("");
    setIsLoading(true);

    try {
      await taskDefinitionAPI.create(taskDefinition as TaskDefinition);
      navigate("/settings/task-definitions");
    } catch (err: any) {
      setError(err?.message || "Failed to create task definition");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Page>
      <div class="min-h-screen bg-neutral-50 flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-sm">
          <h1 class="text-2xl font-medium text-neutral-900 text-center mb-8">
            Create Task Definition
          </h1>

          <TaskDefinitionForm
            onSubmit={handleSubmit}
            isLoading={isLoading()}
            error={error()}
          />
        </div>
      </div>
    </Page>
  );
}

