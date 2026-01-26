import { useNavigate, useParams } from "@solidjs/router";
import {
  Component,
  For,
  Show,
  createEffect,
  createMemo,
  createResource,
  createSignal,
} from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import TriggerForm from "@/components/triggers/Form";
import { tacticAPI, triggerAPI } from "@/utils/api";
import { Tactic, Trigger } from "@/types/api";

const TriggerDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [isDirty, setIsDirty] = createSignal(false);
  const [tacticsError, setTacticsError] = createSignal("");
  const [isTacticsLoading, setIsTacticsLoading] = createSignal(false);
  const [selectedTacticIds, setSelectedTacticIds] = createSignal<string[]>([]);
  const [hasInitializedSelection, setHasInitializedSelection] =
    createSignal(false);

  const [trigger] = createResource<Trigger | undefined, string>(
    () => params.id,
    async (id) => triggerAPI.get(id)
  );

  const [tactics] = createResource<Tactic[]>(tacticAPI.getAll);

  const [linkedTactics, { mutate: mutateLinkedTactics }] = createResource<
    Tactic[] | undefined,
    string
  >(() => params.id, async (id) => triggerAPI.getTactics(id));

  createEffect(() => {
    const current = linkedTactics();
    if (!current || hasInitializedSelection()) return;
    setSelectedTacticIds(
      current.flatMap((tactic) => (tactic.id ? [tactic.id] : []))
    );
    setHasInitializedSelection(true);
  });

  const serializeTrigger = (value: Partial<Trigger>) =>
    JSON.stringify({
      name: (value.name ?? "").trim(),
      description: (value.description ?? "").trim(),
    });

  const initialSignature = createMemo(() => {
    const current = trigger();
    if (!current) return null;
    return serializeTrigger(current);
  });

  const handleFormChange = (value: Partial<Trigger>) => {
    const baseline = initialSignature();
    if (!baseline) return;
    setIsDirty(serializeTrigger(value) !== baseline);
  };

  const handleUpdate = async (partialTrigger: Partial<Trigger>) => {
    const current = trigger();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await triggerAPI.update({
        ...current,
        ...partialTrigger,
        id: current.id,
      });
      navigate("/me/settings/triggers");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update trigger";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = trigger();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await triggerAPI.delete(current.id);
      navigate("/me/settings/triggers");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete trigger";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTactic = (tacticId: string) => {
    setSelectedTacticIds((prev) =>
      prev.includes(tacticId)
        ? prev.filter((id) => id !== tacticId)
        : [...prev, tacticId]
    );
  };

  const handleUpdateTactics = async () => {
    const current = trigger();
    if (!current?.id) return;

    setTacticsError("");
    setIsTacticsLoading(true);
    try {
      const updated = await triggerAPI.updateTactics(
        current.id,
        selectedTacticIds()
      );
      mutateLinkedTactics(updated);
      setSelectedTacticIds(
        updated.flatMap((tactic) => (tactic.id ? [tactic.id] : []))
      );
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update tactics";
      setTacticsError(message);
    } finally {
      setIsTacticsLoading(false);
    }
  };

  return (
    <Show
      when={trigger()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <SettingsPage
          heading="Edit Trigger"
          bottomLink={{
            label: "Back to Triggers",
            url: "/me/settings/triggers",
          }}
        >
          <div class="space-y-6">
            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Trigger
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
                    form="trigger-form"
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
                    Delete trigger
                  </button>
                </div>
              </div>
            </div>

            <TriggerForm
              formId="trigger-form"
              initialData={current()}
              onSubmit={handleUpdate}
              onChange={handleFormChange}
              isLoading={isLoading()}
              error={error()}
              showSubmitButton={false}
            />

            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
              <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div class="text-lg font-semibold text-stone-800">
                    Linked tactics
                  </div>
                  <div class="text-sm text-stone-500">
                    Select the tactics that pair with this trigger.
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleUpdateTactics}
                  disabled={isTacticsLoading()}
                  class="w-full sm:w-auto rounded-full bg-stone-900 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isTacticsLoading() ? "Saving..." : "Save tactics"}
                </button>
              </div>

              <Show
                when={tactics()}
                fallback={
                  <div class="text-sm text-neutral-500">Loading tactics...</div>
                }
              >
                <Show
                  when={tactics()!.length > 0}
                  fallback={
                    <div class="text-sm text-neutral-500">
                      No tactics available yet.
                    </div>
                  }
                >
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <For each={tactics()!.filter((tactic) => tactic.id)}>
                      {(tactic) => (
                        <label class="flex items-start gap-3 rounded-lg border border-neutral-200 bg-white px-4 py-3 text-sm text-neutral-800">
                          <input
                            type="checkbox"
                            class="mt-1 h-4 w-4 rounded border-neutral-300 text-stone-900 focus:ring-stone-800"
                            checked={selectedTacticIds().includes(tactic.id!)}
                            onChange={() => toggleTactic(tactic.id!)}
                          />
                          <div>
                            <div class="font-medium">{tactic.name}</div>
                            <Show when={tactic.description}>
                              <div class="text-xs text-neutral-500">
                                {tactic.description}
                              </div>
                            </Show>
                          </div>
                        </label>
                      )}
                    </For>
                  </div>
                </Show>
              </Show>

              <Show when={tacticsError()}>
                <div class="text-sm text-red-600">{tacticsError()}</div>
              </Show>
            </div>
          </div>
        </SettingsPage>
      )}
    </Show>
  );
};

export default TriggerDetailPage;
