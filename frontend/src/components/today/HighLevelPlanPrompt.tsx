import { Component, Show, For, createEffect, createSignal } from "solid-js";
import { dayAPI } from "@/utils/api";
import { useStreamingData } from "@/providers/streamingData";
import { Icon } from "@/components/shared/Icon";

type HighLevelPlanPromptProps = {
  onSaved?: () => void;
};

export const HighLevelPlanPrompt: Component<HighLevelPlanPromptProps> = (
  props
) => {
  const { day, sync } = useStreamingData();
  const [title, setTitle] = createSignal("");
  const [text, setText] = createSignal("");
  const [intentions, setIntentions] = createSignal<string[]>([]);
  const [newIntention, setNewIntention] = createSignal("");
  const [isDirty, setIsDirty] = createSignal(false);
  const [isSaving, setIsSaving] = createSignal(false);
  const [error, setError] = createSignal("");
  const [lastDate, setLastDate] = createSignal<string | null>(null);

  createEffect(() => {
    const currentDay = day();
    if (!currentDay || isDirty()) return;
    const plan = currentDay.high_level_plan;
    setTitle(plan?.title ?? "");
    setText(plan?.text ?? "");
    setIntentions(plan?.intentions ?? []);
  });

  createEffect(() => {
    const currentDate = day()?.date ?? null;
    if (!currentDate || currentDate === lastDate()) return;
    setLastDate(currentDate);
    setIsDirty(false);
    setError("");
  });

  const handleAddIntention = () => {
    const trimmed = newIntention().trim();
    if (!trimmed) return;
    setIntentions([...intentions(), trimmed]);
    setNewIntention("");
    setIsDirty(true);
  };

  const handleRemoveIntention = (index: number) => {
    setIntentions(intentions().filter((_, i) => i !== index));
    setIsDirty(true);
  };

  const handleSave = async () => {
    if (isSaving()) return;
    setIsSaving(true);
    setError("");

    const trimmedTitle = title().trim();
    const trimmedText = text().trim();

    try {
      const currentDay = day();
      if (!currentDay?.id) {
        setError("Day is not available yet.");
        return;
      }
      await dayAPI.updateDay(currentDay.id, {
        high_level_plan: {
          title: trimmedTitle || null,
          text: trimmedText || null,
          intentions: intentions(),
        },
      });
      setIsDirty(false);
      // Trigger sync to ensure data is fresh
      sync();
      props.onSaved?.();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to update plan";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  if (!day()) return null;

  return (
    <div class="mb-6 rounded-2xl border border-amber-100/80 bg-white/70 shadow-lg shadow-amber-900/5 backdrop-blur-sm p-4 space-y-4">
      <div>
        <p class="text-[11px] uppercase tracking-wide text-amber-700">
          High level plan
        </p>
        <h2 class="text-lg font-medium text-stone-900">
          What does today look like?
        </h2>
        <p class="text-sm text-stone-500">
          Adjust the template plan before you dive in.
        </p>
      </div>

      <div class="space-y-3">
        <input
          class="w-full rounded-lg border border-amber-100/80 bg-white px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-200"
          placeholder="Plan title"
          value={title()}
          onInput={(e) => {
            setTitle(e.currentTarget.value);
            setIsDirty(true);
          }}
        />
        <textarea
          class="w-full rounded-lg border border-amber-100/80 bg-white px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-200"
          placeholder="Plan notes"
          rows={4}
          value={text()}
          onInput={(e) => {
            setText(e.currentTarget.value);
            setIsDirty(true);
          }}
        />
      </div>

      <div class="space-y-2">
        <label class="block text-xs font-medium text-amber-700">
          Intentions
        </label>
        <Show when={intentions().length > 0}>
          <ul class="space-y-1 mb-2">
            <For each={intentions()}>
              {(intention, index) => (
                <li class="flex items-center gap-2 text-sm text-stone-700 bg-amber-50/50 rounded-lg px-3 py-2">
                  <span class="flex-1">{intention}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveIntention(index())}
                    class="text-amber-600 hover:text-amber-700"
                    aria-label="Remove intention"
                  >
                    <Icon key="xMark" class="w-4 h-4" />
                  </button>
                </li>
              )}
            </For>
          </ul>
        </Show>
        <div class="flex gap-2">
          <input
            type="text"
            class="flex-1 rounded-lg border border-amber-100/80 bg-white px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-200"
            placeholder="Add an intention..."
            value={newIntention()}
            onInput={(e) => setNewIntention(e.currentTarget.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleAddIntention();
              }
            }}
          />
          <button
            type="button"
            onClick={handleAddIntention}
            disabled={!newIntention().trim()}
            class="px-3 py-2 rounded-lg bg-amber-100 text-amber-700 hover:bg-amber-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
            aria-label="Add intention"
          >
            <Icon key="plus" class="w-4 h-4" />
          </button>
        </div>
      </div>

      <Show when={error()}>
        <p class="text-xs text-rose-600">{error()}</p>
      </Show>

      <div class="flex items-center gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving()}
          class="flex-1 rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-700 disabled:opacity-60"
        >
          {isSaving() ? "Saving..." : "Save plan"}
        </button>
      </div>
    </div>
  );
};

export default HighLevelPlanPrompt;
