import { Component, Show, For, createEffect, createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import { dayAPI } from "@/utils/api";
import { useStreamingData } from "@/providers/streamingData";
import { Icon } from "@/components/shared/Icon";

const formatTimeForInput = (value?: string | null): string => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
};

const buildIsoDateTime = (dayDate: string, timeValue: string): string | null => {
  const trimmedValue = timeValue.trim();
  if (!trimmedValue) return null;
  const [year, month, day] = dayDate.split("-").map(Number);
  const [hours, minutes] = trimmedValue.split(":").map(Number);
  if (
    Number.isNaN(year) ||
    Number.isNaN(month) ||
    Number.isNaN(day) ||
    Number.isNaN(hours) ||
    Number.isNaN(minutes)
  ) {
    return null;
  }
  const localDate = new Date(year, month - 1, day, hours, minutes, 0, 0);
  return localDate.toISOString();
};

export const TodayEditPage: Component = () => {
  const navigate = useNavigate();
  const { day, sync } = useStreamingData();
  const [startsAt, setStartsAt] = createSignal("");
  const [endsAt, setEndsAt] = createSignal("");
  const [planTitle, setPlanTitle] = createSignal("");
  const [planText, setPlanText] = createSignal("");
  const [intentions, setIntentions] = createSignal<string[]>([]);
  const [newIntention, setNewIntention] = createSignal("");
  const [isDirty, setIsDirty] = createSignal(false);
  const [isSaving, setIsSaving] = createSignal(false);
  const [error, setError] = createSignal("");
  const [lastDate, setLastDate] = createSignal<string | null>(null);

  createEffect(() => {
    const currentDay = day();
    if (!currentDay || isDirty()) return;
    setStartsAt(formatTimeForInput(currentDay.starts_at));
    setEndsAt(formatTimeForInput(currentDay.ends_at));
    const plan = currentDay.high_level_plan;
    setPlanTitle(plan?.title ?? "");
    setPlanText(plan?.text ?? "");
    setIntentions(plan?.intentions ?? []);
  });

  createEffect(() => {
    const currentDate = day()?.date ?? null;
    if (!currentDate || currentDate === lastDate()) return;
    setLastDate(currentDate);
    setIsDirty(false);
    setError("");
  });

  const handleSave = async () => {
    if (isSaving()) return;
    setIsSaving(true);
    setError("");

    try {
      const currentDay = day();
      if (!currentDay?.id) {
        setError("Day is not available yet.");
        return;
      }

      const startsAtValue = buildIsoDateTime(currentDay.date, startsAt());
      const endsAtValue = buildIsoDateTime(currentDay.date, endsAt());
      const trimmedTitle = planTitle().trim();
      const trimmedText = planText().trim();

      await dayAPI.updateDay(currentDay.id, {
        starts_at: startsAtValue ?? null,
        ends_at: endsAtValue ?? null,
        high_level_plan: {
          title: trimmedTitle || null,
          text: trimmedText || null,
          intentions: intentions(),
        },
      });

      setIsDirty(false);
      // Trigger sync to ensure data is fresh
      sync();
      navigate("/me");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to update day";
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  if (!day()) return null;

  return (
    <div class="max-w-2xl">
      <div class="rounded-2xl border border-amber-100/80 bg-white/70 shadow-lg shadow-amber-900/5 backdrop-blur-sm p-4 space-y-5">
        <div>
          <p class="text-[11px] uppercase tracking-wide text-amber-700">
            Today editor
          </p>
          <h2 class="text-lg font-medium text-stone-900">
            Update your day basics
          </h2>
          <p class="text-sm text-stone-500">
            Adjust your start, end, and plan details.
          </p>
        </div>

        <div class="space-y-3">
          <div class="space-y-2">
            <label
              class="text-xs font-semibold uppercase tracking-wide text-stone-500"
              for="starts-at"
            >
              Starts at
            </label>
            <input
              id="starts-at"
              type="time"
              class="w-full rounded-lg border border-amber-100/80 bg-white px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-200"
              value={startsAt()}
              onInput={(e) => {
                setStartsAt(e.currentTarget.value);
                setIsDirty(true);
              }}
            />
          </div>

          <div class="space-y-2">
            <label
              class="text-xs font-semibold uppercase tracking-wide text-stone-500"
              for="ends-at"
            >
              Ends at
            </label>
            <input
              id="ends-at"
              type="time"
              class="w-full rounded-lg border border-amber-100/80 bg-white px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-200"
              value={endsAt()}
              onInput={(e) => {
                setEndsAt(e.currentTarget.value);
                setIsDirty(true);
              }}
            />
          </div>
        </div>

        <div class="space-y-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-stone-500">
              High level plan
            </p>
          </div>
          <input
            class="w-full rounded-lg border border-amber-100/80 bg-white px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-200"
            placeholder="Plan title"
            value={planTitle()}
            onInput={(e) => {
              setPlanTitle(e.currentTarget.value);
              setIsDirty(true);
            }}
          />
          <textarea
            class="w-full rounded-lg border border-amber-100/80 bg-white px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-200"
            placeholder="Plan notes"
            rows={4}
            value={planText()}
            onInput={(e) => {
              setPlanText(e.currentTarget.value);
              setIsDirty(true);
            }}
          />

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
                        onClick={() => {
                          setIntentions(intentions().filter((_, i) => i !== index()));
                          setIsDirty(true);
                        }}
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
                    const trimmed = newIntention().trim();
                    if (trimmed) {
                      setIntentions([...intentions(), trimmed]);
                      setNewIntention("");
                      setIsDirty(true);
                    }
                  }
                }}
              />
              <button
                type="button"
                onClick={() => {
                  const trimmed = newIntention().trim();
                  if (trimmed) {
                    setIntentions([...intentions(), trimmed]);
                    setNewIntention("");
                    setIsDirty(true);
                  }
                }}
                disabled={!newIntention().trim()}
                class="px-3 py-2 rounded-lg bg-amber-100 text-amber-700 hover:bg-amber-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                aria-label="Add intention"
              >
                <Icon key="plus" class="w-4 h-4" />
              </button>
            </div>
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
            {isSaving() ? "Saving..." : "Save changes"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TodayEditPage;
