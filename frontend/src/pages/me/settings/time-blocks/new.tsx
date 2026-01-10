import { createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import SettingsPage from "@/components/shared/SettingsPage";
import TimeBlockDefinitionForm from "@/components/time-blocks/Form";
import { timeBlockDefinitionAPI } from "@/utils/api";
import { TimeBlockDefinition } from "@/types/api";

export default function NewTimeBlock() {
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (timeBlockDefinition: Partial<TimeBlockDefinition>) => {
    setError("");
    setIsLoading(true);

    try {
      await timeBlockDefinitionAPI.create(
        timeBlockDefinition as TimeBlockDefinition
      );
      navigate("/me/settings/time-blocks");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create time block";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SettingsPage
      heading="Create Time Block"
      bottomLink={{ label: "Back to Time Blocks", url: "/me/settings/time-blocks" }}
    >
      <div class="flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-xl">
          <TimeBlockDefinitionForm
            onSubmit={handleSubmit}
            isLoading={isLoading()}
            error={error()}
          />
        </div>
      </div>
    </SettingsPage>
  );
}

