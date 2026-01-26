import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createMemo, createResource, createSignal } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import TimeBlockDefinitionForm from "@/components/time-blocks/Form";
import { timeBlockDefinitionAPI } from "@/utils/api";
import { TimeBlockDefinition } from "@/types/api";

const TimeBlockDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [isDirty, setIsDirty] = createSignal(false);

  const [timeBlockDefinition] = createResource<TimeBlockDefinition | undefined, string>(
    () => params.id,
    async (id) => {
      return await timeBlockDefinitionAPI.get(id);
    }
  );

  const serializeTimeBlockDefinition = (value: Partial<TimeBlockDefinition>) =>
    JSON.stringify({
      name: (value.name ?? "").trim(),
      description: (value.description ?? "").trim(),
      type: value.type ?? "WORK",
      category: value.category ?? "WORK",
    });

  const initialSignature = createMemo(() => {
    const current = timeBlockDefinition();
    if (!current) return null;
    return serializeTimeBlockDefinition(current);
  });

  const handleFormChange = (value: Partial<TimeBlockDefinition>) => {
    const baseline = initialSignature();
    if (!baseline) return;
    setIsDirty(serializeTimeBlockDefinition(value) !== baseline);
  };

  const handleUpdate = async (partialTimeBlockDefinition: Partial<TimeBlockDefinition>) => {
    const current = timeBlockDefinition();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await timeBlockDefinitionAPI.update({
        ...current,
        ...partialTimeBlockDefinition,
        id: current.id,
      });
      navigate("/me/settings/time-blocks");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update time block";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = timeBlockDefinition();
    if (!current || !current.id) return;
    setError("");
    setIsLoading(true);
    try {
      await timeBlockDefinitionAPI.delete(current.id);
      navigate("/me/settings/time-blocks");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete time block";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Show
      when={timeBlockDefinition()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <SettingsPage
          heading="Edit Time Block"
          bottomLink={{ label: "Back to Time Blocks", url: "/me/settings/time-blocks" }}
        >
          <div class="space-y-6">
            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Time Block
                  </div>
                  <div class="text-lg font-semibold text-stone-800">
                    {current().name}
                  </div>
                  <Show
                    when={isDirty()}
                    fallback={
                      <div class="text-xs text-stone-400">All changes saved</div>
                    }
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
                    form="time-block-definition-form"
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
                    Delete time block
                  </button>
                </div>
              </div>
            </div>

            <TimeBlockDefinitionForm
              formId="time-block-definition-form"
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

export default TimeBlockDetailPage;

