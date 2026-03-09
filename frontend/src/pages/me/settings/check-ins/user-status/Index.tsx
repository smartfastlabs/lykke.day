import {
  Component,
  For,
  Show,
  createEffect,
  createResource,
  createSignal,
} from "solid-js";
import UseCaseConfigPageLayout from "@/components/settings/UseCaseConfigPageLayout";
import { globalNotifications } from "@/providers/notifications";
import type {
  CurrentUser,
  LLMRunResultSnapshot,
  StatusSignal,
  UserStatusCheckInPreview,
} from "@/types/api";
import { authAPI, usecaseConfigAPI } from "@/utils/api";

const USER_STATUS_USECASE = "user_status_use_case";
const DEFAULT_USER_STATUS_SIGNALS: StatusSignal[] = [
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

type EditableSignal = {
  name: string;
  slug: string;
  description: string;
  goal_text: string;
  goal_value: string;
};

const slugify = (value: string): string =>
  value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

const normalizeStatusSignals = (signals: unknown): EditableSignal[] => {
  if (!Array.isArray(signals)) {
    return DEFAULT_USER_STATUS_SIGNALS.map((signal) => ({
      name: signal.name,
      slug: signal.slug,
      description: signal.description ?? "",
      goal_text: signal.goal.text ?? "",
      goal_value:
        signal.goal.value !== null && signal.goal.value !== undefined
          ? String(signal.goal.value)
          : "",
    }));
  }

  const deduped: EditableSignal[] = [];
  const seen = new Set<string>();
  for (const signal of signals) {
    let name = "";
    let slug = "";
    let description = "";
    let goalText = "";
    let goalValue = "";
    if (typeof signal === "string") {
      const cleaned = signal.trim();
      if (!cleaned) continue;
      if (cleaned.includes(":")) {
        const [namePart, descriptionPart] = cleaned.split(":", 2);
        name = namePart.trim();
        description = descriptionPart.trim();
      } else {
        name = cleaned;
      }
    } else if (signal && typeof signal === "object") {
      const nameCandidate =
        "name" in signal && typeof signal.name === "string"
          ? signal.name.trim()
          : "";
      const slugCandidate =
        "slug" in signal && typeof signal.slug === "string"
          ? signal.slug.trim()
          : "";
      const descriptionCandidate =
        "description" in signal && typeof signal.description === "string"
          ? signal.description.trim()
          : "";
      const goalCandidate = "goal" in signal ? signal.goal : undefined;
      name = nameCandidate;
      slug = slugCandidate;
      description = descriptionCandidate;
      if (goalCandidate && typeof goalCandidate === "object") {
        goalText =
          "text" in goalCandidate && typeof goalCandidate.text === "string"
            ? goalCandidate.text.trim()
            : "";
        goalValue =
          "value" in goalCandidate &&
          (typeof goalCandidate.value === "number" ||
            typeof goalCandidate.value === "string")
            ? String(goalCandidate.value)
            : "";
      }
    }

    if (!name) continue;
    slug = slugify(slug || name);
    if (!slug) continue;
    const key = slug.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push({
      name,
      slug,
      description,
      goal_text: goalText,
      goal_value: goalValue,
    });
  }

  return deduped.length
    ? deduped
    : DEFAULT_USER_STATUS_SIGNALS.map((signal) => ({
        name: signal.name,
        slug: signal.slug,
        description: signal.description ?? "",
        goal_text: signal.goal.text ?? "",
        goal_value:
          signal.goal.value !== null && signal.goal.value !== undefined
            ? String(signal.goal.value)
            : "",
      }));
};

const UserStatusUseCaseCheckInConfigPage: Component = () => {
  const [config, { mutate }] = createResource(() =>
    usecaseConfigAPI.getConfigForUseCaseWithStatus(USER_STATUS_USECASE, {
      user_amendments: [],
    }),
  );
  const [currentUser, { refetch: refetchCurrentUser }] = createResource<CurrentUser | null>(
    () => authAPI.me(),
  );
  const [snapshotPreview, { refetch: refetchSnapshotPreview }] =
    createResource<LLMRunResultSnapshot | null>(() =>
      usecaseConfigAPI.getLLMSnapshotPreviewForUseCase(USER_STATUS_USECASE),
    );
  const [amendments, setAmendments] = createSignal<string[]>([]);
  const [statusSignals, setStatusSignals] = createSignal<EditableSignal[]>(
    DEFAULT_USER_STATUS_SIGNALS.map((signal) => ({
      name: signal.name,
      slug: signal.slug,
      description: signal.description ?? "",
      goal_text: signal.goal.text ?? "",
      goal_value:
        signal.goal.value !== null && signal.goal.value !== undefined
          ? String(signal.goal.value)
          : "",
    })),
  );
  const [isConfigured, setIsConfigured] = createSignal(false);
  const [isSaving, setIsSaving] = createSignal(false);
  const [isPreviewing, setIsPreviewing] = createSignal(false);
  const [previewResult, setPreviewResult] = createSignal<UserStatusCheckInPreview | null>(null);
  const [error, setError] = createSignal("");

  createEffect(() => {
    const configData = config();
    if (!configData) {
      if (!config.loading && config.error) {
        const err = config.error;
        if (err instanceof Error) {
          setError(err.message);
        }
      }
      return;
    }

    setIsConfigured(configData.exists);
    setAmendments([...(configData.config.user_amendments ?? [])]);
    setError("");
  });

  createEffect(() => {
    const userData = currentUser();
    if (!userData) return;
    setStatusSignals(normalizeStatusSignals(userData.settings?.status_signals));
  });

  const addStatusSignal = () => {
    setStatusSignals((current) => [
      ...current,
      { name: "", slug: "", description: "", goal_text: "", goal_value: "" },
    ]);
  };

  const removeStatusSignal = (index: number) => {
    setStatusSignals((current) => current.filter((_, idx) => idx !== index));
  };

  const updateStatusSignal = (
    index: number,
    key: keyof EditableSignal,
    value: string,
  ) => {
    setStatusSignals((current) =>
      current.map((signal, idx) =>
        idx === index ? { ...signal, [key]: value } : signal,
      ),
    );
  };

  const sanitizedStatusSignals = (): StatusSignal[] =>
    normalizeStatusSignals(statusSignals()).map((signal) => ({
      name: signal.name,
      slug: slugify(signal.slug || signal.name),
      description: signal.description,
      goal: {
        text: signal.goal_text,
        value: (() => {
          if (signal.goal_value.trim().length === 0) {
            return null;
          }
          const parsed = Number.parseFloat(signal.goal_value);
          return Number.isFinite(parsed) ? parsed : null;
        })(),
      },
    }));

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      const wasConfigured = isConfigured();
      await authAPI.updateProfile({
        settings: {
          status_signals: sanitizedStatusSignals(),
        },
      });
      const updated = await usecaseConfigAPI.updateConfigForUseCase(
        USER_STATUS_USECASE,
        {
          user_amendments: amendments(),
        },
      );
      mutate({ config: updated, exists: true });
      await refetchCurrentUser();
      setIsConfigured(true);
      refetchSnapshotPreview();
      globalNotifications.addSuccess(
        wasConfigured
          ? "User status check-in settings saved successfully"
          : "User status check-in enabled",
      );
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to save settings";
      setError(errorMessage);
      globalNotifications.addError(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRunPreview = async () => {
    setIsPreviewing(true);
    setError("");
    try {
      const result = await usecaseConfigAPI.runUserStatusCheckInPreview();
      setPreviewResult(result);
      if (!result) {
        globalNotifications.addError(
          "No preview result available. Check your LLM provider settings.",
        );
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to run check-in preview";
      setError(errorMessage);
      globalNotifications.addError(errorMessage);
    } finally {
      setIsPreviewing(false);
    }
  };

  return (
    <UseCaseConfigPageLayout
      heading="User Status Check-In"
      error={error()}
      isLoading={config.loading}
      isSaving={isSaving()}
      amendments={amendments()}
      onAmendmentsChange={setAmendments}
      onSave={handleSave}
      snapshotPreview={snapshotPreview()}
      snapshotLoading={snapshotPreview.loading}
      saveButtonLabel={
        isConfigured() ? "Save Changes" : "Enable User Status Check-In"
      }
      amendmentsDescription="Add custom instructions that will be appended to the default user status check-in prompt."
    >
      <Show when={!isConfigured()}>
        <div class="rounded-lg border border-emerald-200 bg-emerald-50 p-5 space-y-3">
          <h2 class="text-lg font-semibold text-emerald-900">
            Enable User Status Check-In
          </h2>
          <p class="text-sm text-emerald-800">
            Turn this on to have Lykke generate reflective check-ins using your
            day context. Start by choosing the status signals you want scored, then
            save.
          </p>
          <button
            type="button"
            onClick={() => handleSave()}
            disabled={isSaving() || config.loading}
            class="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving() ? "Enabling..." : "Enable Now"}
          </button>
        </div>
      </Show>

      <div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm space-y-4">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Status signals to score</h2>
            <p class="text-sm text-gray-600">
              Define each signal with a name, slug, description, and optional goal.
            </p>
          </div>
          <button
            type="button"
            onClick={addStatusSignal}
            disabled={isSaving() || config.loading}
            class="px-3 py-2 rounded-md border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
          >
            + Add Signal
          </button>
        </div>

        <div class="space-y-3">
          <For each={statusSignals()}>
            {(signal, index) => (
              <div class="rounded-md border border-gray-200 p-3 bg-gray-50/40">
                <div class="grid grid-cols-1 md:grid-cols-[180px_160px_1fr_1fr_120px_auto] gap-3 items-start">
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">
                      Name
                    </label>
                    <input
                      type="text"
                      value={signal.name}
                      onInput={(event) =>
                        updateStatusSignal(index(), "name", event.currentTarget.value)
                      }
                      placeholder="e.g. Anxiety"
                      disabled={isSaving() || config.loading}
                      class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                    />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">
                      Slug
                    </label>
                    <input
                      type="text"
                      value={signal.slug}
                      onInput={(event) =>
                        updateStatusSignal(index(), "slug", event.currentTarget.value)
                      }
                      placeholder="e.g. anxiety"
                      disabled={isSaving() || config.loading}
                      class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                    />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">
                      Description
                    </label>
                    <input
                      type="text"
                      value={signal.description}
                      onInput={(event) =>
                        updateStatusSignal(
                          index(),
                          "description",
                          event.currentTarget.value,
                        )
                      }
                      placeholder="What this signal should represent"
                      disabled={isSaving() || config.loading}
                      class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                    />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">
                      Goal text
                    </label>
                    <input
                      type="text"
                      value={signal.goal_text}
                      onInput={(event) =>
                        updateStatusSignal(
                          index(),
                          "goal_text",
                          event.currentTarget.value,
                        )
                      }
                      placeholder="Describe your target"
                      disabled={isSaving() || config.loading}
                      class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                    />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">
                      Goal value
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={signal.goal_value}
                      onInput={(event) =>
                        updateStatusSignal(
                          index(),
                          "goal_value",
                          event.currentTarget.value,
                        )
                      }
                      placeholder="0-100"
                      disabled={isSaving() || config.loading}
                      class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                    />
                  </div>
                  <div class="pt-6">
                    <button
                      type="button"
                      onClick={() => removeStatusSignal(index())}
                      disabled={
                        isSaving() || config.loading || statusSignals().length <= 1
                      }
                      class="px-3 py-2 rounded-md border border-red-200 text-red-700 text-sm hover:bg-red-50 disabled:text-gray-300 disabled:border-gray-200 disabled:bg-white"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </div>
            )}
          </For>
        </div>
      </div>

      <Show when={isConfigured()}>
        <div class="rounded-2xl border border-emerald-100/80 bg-white/80 p-5 shadow-sm shadow-emerald-900/5 space-y-4">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="text-lg font-semibold mb-2">Generated Check-In Preview</h2>
              <p class="text-sm text-gray-600">
                Run a dry preview to see what check-in text and scores would be
                generated right now.
              </p>
            </div>
            <button
              type="button"
              onClick={() => handleRunPreview()}
              disabled={isPreviewing() || isSaving() || config.loading}
              class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isPreviewing() ? "Running..." : "Run Check-In Preview"}
            </button>
          </div>

          <Show
            when={previewResult()}
            fallback={
              <div class="text-sm text-stone-500">
                Run preview to see the generated check-in output.
              </div>
            }
          >
            {(preview) => (
              <div class="space-y-3">
                <div>
                  <h3 class="text-sm font-semibold text-gray-800">Text</h3>
                  <p class="text-sm text-gray-700">
                    {preview().text?.trim() || "No text generated."}
                  </p>
                </div>
                <div>
                  <h3 class="text-sm font-semibold text-gray-800">Scores</h3>
                  <pre class="rounded-md bg-stone-100 p-3 text-xs text-stone-800 overflow-auto">
                    {JSON.stringify(preview().scores ?? {}, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </Show>
        </div>
      </Show>
    </UseCaseConfigPageLayout>
  );
};

export default UserStatusUseCaseCheckInConfigPage;
