import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import Page from "@/components/shared/layout/page";
import RoutineForm from "@/components/routines/form";
import { routineAPI } from "@/utils/api";
import { Routine } from "@/types/api";

const RoutineDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const [routine] = createResource<Routine | undefined, string>(
    () => params.id,
    async (id) => {
      console.log("LOADING ROUTINE", id);

      return await routineAPI.get(id);
    }
  );

  const handleUpdate = async (partialRoutine: Partial<Routine>) => {
    const current = routine();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await routineAPI.update({
        ...current,
        ...partialRoutine,
        id: current.id,
      });
      navigate("/settings/routines");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update routine";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = routine();
    if (!current || !current.id) return;
    setError("");
    setIsLoading(true);
    try {
      await routineAPI.delete(current.id);
      navigate("/settings/routines");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete routine";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Page>
      <Show
        when={routine()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        {(current) => (
          <div class="min-h-screen bg-neutral-50 flex flex-col items-center justify-center px-6">
            <div class="w-full max-w-sm space-y-6">
              <div class="flex items-center justify-between">
                <h1 class="text-2xl font-medium text-neutral-900">
                  Edit Routine
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

              <RoutineForm
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

export default RoutineDetailPage;
