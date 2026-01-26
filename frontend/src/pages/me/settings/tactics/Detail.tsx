import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createMemo, createResource, createSignal } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import TacticForm from "@/components/tactics/Form";
import { tacticAPI } from "@/utils/api";
import { Tactic } from "@/types/api";

const TacticDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [isDirty, setIsDirty] = createSignal(false);

  const [tactic] = createResource<Tactic | undefined, string>(
    () => params.id,
    async (id) => tacticAPI.get(id)
  );

  const serializeTactic = (value: Partial<Tactic>) =>
    JSON.stringify({
      name: (value.name ?? "").trim(),
      description: (value.description ?? "").trim(),
    });

  const initialSignature = createMemo(() => {
    const current = tactic();
    if (!current) return null;
    return serializeTactic(current);
  });

  const handleFormChange = (value: Partial<Tactic>) => {
    const baseline = initialSignature();
    if (!baseline) return;
    setIsDirty(serializeTactic(value) !== baseline);
  };

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
        <SettingsPage
          heading="Edit Tactic"
          bottomLink={{
            label: "Back to Tactics",
            url: "/me/settings/tactics",
          }}
        >
          <div class="space-y-6">
            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Tactic
                  </div>
                  <div class="text-lg font-semibold text-stone-800">
                    {current().name}
                  </div>
                  <Show
                    when={isDirty()}
                    fallback={<div class="text-xs text-stone-400">All changes saved</div>}
                  >
                    <div class="inline-flex items-center gap-2 text-xs font-medium text-amber-700">
                      <span class="h-2 w-2 rounded-full bg-amber-500" />
                      Unsaved changes
                    </div>
                  </Show>
                </div>
                <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <button
                    type="submit"
                    form="tactic-form"
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full bg-stone-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isLoading() ? "Saving..." : "Save changes"}
                  </button>
                  <button
                    type="button"
                    onClick={handleDelete}
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full border border-stone-200 bg-white px-5 py-3 text-sm font-semibold text-stone-600 shadow-sm transition hover:border-stone-300 hover:text-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Delete tactic
                  </button>
                </div>
              </div>
            </div>

            <TacticForm
              formId="tactic-form"
              initialData={current()}
              onSubmit={handleUpdate}
              onChange={handleFormChange}
              isLoading={isLoading()}
              error={error()}
              showSubmitButton={false}
            />
          </div>
        </SettingsPage>
      )}
    </Show>
  );
};

export default TacticDetailPage;
