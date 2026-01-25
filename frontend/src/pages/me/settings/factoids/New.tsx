import { createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import SettingsPage from "@/components/shared/SettingsPage";
import { factoidAPI } from "@/utils/api";
import { Factoid } from "@/types/api";
import FactoidForm from "@/components/factoids/Form";

export default function NewFactoid() {
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (factoid: Partial<Factoid>) => {
    setError("");
    setIsLoading(true);

    try {
      await factoidAPI.create(factoid as Factoid);
      navigate("/me/settings/factoids");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create factoid";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SettingsPage
      heading="Create Factoid"
      bottomLink={{
        label: "Back to Factoids",
        url: "/me/settings/factoids",
      }}
    >
      <div class="flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-sm">
          <FactoidForm
            onSubmit={handleSubmit}
            isLoading={isLoading()}
            error={error()}
          />
        </div>
      </div>
    </SettingsPage>
  );
}
