import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import DetailPage from "@/components/shared/DetailPage";
import TacticForm from "@/components/tactics/Form";
import TacticPreview from "@/components/tactics/Preview";
import { tacticAPI } from "@/utils/api";
import { Tactic } from "@/types/api";

const TacticDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const [tactic] = createResource<Tactic | undefined, string>(
    () => params.id,
    async (id) => tacticAPI.get(id)
  );

  const handleUpdate = async (partialTactic: Partial<Tactic>) => {
    const current = tactic();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await tacticAPI.update({
        ...current,
        ...partialTactic,
        id: current.id,
      });
      navigate("/me/settings/tactics");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update tactic";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = tactic();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await tacticAPI.delete(current.id);
      navigate("/me/settings/tactics");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete tactic";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Show
      when={tactic()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <DetailPage
          heading="Tactic"
          bottomLink={{
            label: "Back to Tactics",
            url: "/me/settings/tactics",
          }}
          preview={<TacticPreview tactic={current()} />}
          edit={
            <div class="flex flex-col items-center justify-center px-6 py-8">
              <div class="w-full max-w-sm space-y-6">
                <TacticForm
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

export default TacticDetailPage;
