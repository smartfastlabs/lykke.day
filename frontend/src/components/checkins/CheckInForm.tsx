import { Component, For, createMemo, createSignal } from "solid-js";
import { FormError, Input, SubmitButton, TextArea } from "@/components/forms";
import { useAuth } from "@/providers/auth";
import { globalNotifications } from "@/providers/notifications";
import type { StatusSignal } from "@/types/api";
import { checkInAPI } from "@/utils/api";

type CheckInFormProps = {
  submitText?: string;
  loadingText?: string;
  onSuccess?: () => void;
  onCancel?: () => void;
};

const DEFAULT_STATUS_SIGNALS: StatusSignal[] = [
  {
    name: "Cravings",
    slug: "cravings",
    description: "Urge intensity and frequency.",
    goal: { text: "", value: null },
  },
  {
    name: "Depression",
    slug: "depression",
    description: "Low mood, hopelessness, and emotional heaviness.",
    goal: { text: "", value: null },
  },
  {
    name: "Anxiety",
    slug: "anxiety",
    description: "Stress, worry, and nervous system activation.",
    goal: { text: "", value: null },
  },
  {
    name: "Mood",
    slug: "mood",
    description: "Overall emotional tone for the day.",
    goal: { text: "", value: null },
  },
  {
    name: "Energy",
    slug: "energy",
    description: "Mental and physical energy availability.",
    goal: { text: "", value: null },
  },
  {
    name: "Focus",
    slug: "focus",
    description: "Attention quality and ability to stay on task.",
    goal: { text: "", value: null },
  },
];

const CheckInForm: Component<CheckInFormProps> = (props) => {
  const { user } = useAuth();
  const [text, setText] = createSignal("");
  const [scoreValues, setScoreValues] = createSignal<Record<string, string>>({});
  const [isSaving, setIsSaving] = createSignal(false);
  const [formError, setFormError] = createSignal("");

  const statusSignals = createMemo(() => {
    const configured = user()?.settings?.status_signals ?? [];
    return configured.length > 0 ? configured : DEFAULT_STATUS_SIGNALS;
  });

  const setSignalScore = (slug: string, value: string) => {
    setScoreValues((current) => ({
      ...current,
      [slug]: value,
    }));
  };

  const parseScores = (): Record<string, number> => {
    const parsed: Record<string, number> = {};
    for (const signal of statusSignals()) {
      const rawValue = (scoreValues()[signal.slug] ?? "").trim();
      if (!rawValue) continue;
      const value = Number(rawValue);
      if (!Number.isFinite(value) || value < 0) {
        throw new Error(`${signal.name} must be a number 0 or greater.`);
      }
      parsed[signal.slug] = value;
    }
    return parsed;
  };

  const handleSubmit = async (event: Event) => {
    event.preventDefault();
    setFormError("");
    const trimmedText = text().trim();

    let scores: Record<string, number>;
    try {
      scores = parseScores();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Invalid score value.");
      return;
    }

    if (!trimmedText && Object.keys(scores).length === 0) {
      setFormError("Add text or rate at least one status signal.");
      return;
    }

    try {
      setIsSaving(true);
      await checkInAPI.create({
        text: trimmedText || undefined,
        scores: Object.keys(scores).length > 0 ? scores : undefined,
      });
      setText("");
      setScoreValues({});
      globalNotifications.addSuccess("Check-in saved.");
      props.onSuccess?.();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to save check-in.";
      setFormError(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form class="space-y-5" onSubmit={handleSubmit}>
      <TextArea
        id="checkin-text"
        placeholder="How are you doing right now? (optional)"
        value={text}
        onChange={setText}
        rows={4}
      />
      <div class="space-y-3">
        <p class="text-xs uppercase tracking-wide text-stone-500">
          Rate any status signals (0 or more)
        </p>
        <For each={statusSignals()}>
          {(signal) => (
            <div class="rounded-lg border border-stone-200 bg-white p-3">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-medium text-stone-800">{signal.name}</p>
                  <p class="text-xs text-stone-500">
                    {signal.description || "No description"}
                  </p>
                </div>
                <div class="w-28">
                  <Input
                    id={`checkin-score-${signal.slug}`}
                    type="number"
                    min="0"
                    inputMode="decimal"
                    placeholder="Skip"
                    value={() => scoreValues()[signal.slug] ?? ""}
                    onChange={(value) => setSignalScore(signal.slug, value)}
                  />
                </div>
              </div>
            </div>
          )}
        </For>
      </div>
      <FormError error={formError()} />
      <div class="flex items-center gap-3">
        <SubmitButton
          isLoading={isSaving()}
          loadingText={props.loadingText ?? "Saving..."}
          text={props.submitText ?? "Save check-in"}
        />
        {props.onCancel && (
          <button
            type="button"
            onClick={() => props.onCancel?.()}
            disabled={isSaving()}
            class="flex-1 h-11 flex items-center justify-center bg-white border border-stone-200 text-stone-700 rounded-lg hover:bg-stone-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
};

export default CheckInForm;
