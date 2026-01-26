import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createMemo, createResource, createSignal } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import FactoidForm from "@/components/factoids/Form";
import { factoidAPI } from "@/utils/api";
import { Factoid } from "@/types/api";

const FactoidDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [isDirty, setIsDirty] = createSignal(false);

  const [factoid] = createResource<Factoid | undefined, string>(
    () => params.id,
    async (id) => factoidAPI.get(id)
  );

  const serializeFactoid = (value: Partial<Factoid>) =>
    JSON.stringify({
      content: (value.content ?? "").trim(),
      factoid_type: value.factoid_type ?? "semantic",
      criticality: value.criticality ?? "normal",
    });

  const initialSignature = createMemo(() => {
    const current = factoid();
    if (!current) return null;
    return serializeFactoid(current);
  });

  const handleFormChange = (value: Partial<Factoid>) => {
    const baseline = initialSignature();
    if (!baseline) return;
    setIsDirty(serializeFactoid(value) !== baseline);
  };

  const handleUpdate = async (partialFactoid: Partial<Factoid>) => {
    const current = factoid();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await factoidAPI.update({
        ...current,
        ...partialFactoid,
        id: current.id,
      });
      navigate("/me/settings/factoids");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update factoid";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = factoid();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await factoidAPI.delete(current.id);
      navigate("/me/settings/factoids");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete factoid";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Show
      when={factoid()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <SettingsPage
          heading="Edit Factoid"
          bottomLink={{
            label: "Back to Factoids",
            url: "/me/settings/factoids",
          }}
        >
          <div class="space-y-6">
            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Factoid
                  </div>
                  <div class="text-lg font-semibold text-stone-800">
                    {current().content.slice(0, 60)}
                    {current().content.length > 60 ? "…" : ""}
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
                    form="factoid-form"
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
                    Delete factoid
                  </button>
                </div>
              </div>
            </div>

            <FactoidForm
              formId="factoid-form"
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

export default FactoidDetailPage;
