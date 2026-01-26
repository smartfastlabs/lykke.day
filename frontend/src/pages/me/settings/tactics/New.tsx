import { createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import SettingsPage from "@/components/shared/SettingsPage";
import { tacticAPI } from "@/utils/api";
import { Tactic } from "@/types/api";
import TacticForm from "@/components/tactics/Form";

export default function NewTactic() {
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (tactic: Partial<Tactic>) => {
    setError("");
    setIsLoading(true);

    try {
      await tacticAPI.create(tactic as Tactic);
      navigate("/me/settings/tactics");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create tactic";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SettingsPage
      heading="Create Tactic"
      bottomLink={{
        label: "Back to Tactics",
        url: "/me/settings/tactics",
      }}
    >
      <div class="flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-sm">
          <TacticForm
            onSubmit={handleSubmit}
            isLoading={isLoading()}
            error={error()}
          />
        </div>
      </div>
    </SettingsPage>
  );
}
