import { createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import SettingsPage from "@/components/shared/settingsPage";
import { taskDefinitionAPI } from "@/utils/api";
import { TaskDefinition } from "@/types/api";
import TaskDefinitionForm from "@/components/taskDefinitions/form";

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
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to create task definition";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SettingsPage
      heading="Create Task Definition"
      bottomLink={{ label: "Back to Task Definitions", url: "/settings/task-definitions" }}
    >
      <div class="flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-sm">
          <TaskDefinitionForm
            onSubmit={handleSubmit}
            isLoading={isLoading()}
            error={error()}
          />
        </div>
      </div>
    </SettingsPage>
  );
}

