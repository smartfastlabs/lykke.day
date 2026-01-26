import { createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import SettingsPage from "@/components/shared/SettingsPage";
import { triggerAPI } from "@/utils/api";
import { Trigger } from "@/types/api";
import TriggerForm from "@/components/triggers/Form";

export default function NewTrigger() {
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (trigger: Partial<Trigger>) => {
    setError("");
    setIsLoading(true);

    try {
      await triggerAPI.create(trigger as Trigger);
      navigate("/me/settings/triggers");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create trigger";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SettingsPage
      heading="Create Trigger"
      bottomLink={{
        label: "Back to Triggers",
        url: "/me/settings/triggers",
      }}
    >
      <div class="flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-sm">
          <TriggerForm
            onSubmit={handleSubmit}
            isLoading={isLoading()}
            error={error()}
          />
        </div>
      </div>
    </SettingsPage>
  );
}
