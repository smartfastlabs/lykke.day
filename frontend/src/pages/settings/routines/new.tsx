import { createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import Page from "../../../components/shared/layout/page";
import { routineAPI } from "../../../utils/api";
import { Routine } from "../../../types/api";
import RoutineForm from "../../../components/routines/form";

export default function NewRoutine() {
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (routine: Partial<Routine>) => {
    setError("");
    setIsLoading(true);

    try {
      await routineAPI.create(routine as Routine);
      navigate("/settings/routines");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create routine";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Page>
      <div class="min-h-screen bg-neutral-50 flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-sm">
          <h1 class="text-2xl font-medium text-neutral-900 text-center mb-8">
            Create Routine
          </h1>

          <RoutineForm onSubmit={handleSubmit} isLoading={isLoading()} error={error()} />
        </div>
      </div>
    </Page>
  );
}


