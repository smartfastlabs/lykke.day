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
  LLMRunResultSnapshot,
  UseCaseMetric,
  UserStatusCheckInPreview,
} from "@/types/api";
import { usecaseConfigAPI } from "@/utils/api";

const USER_STATUS_USECASE = "user_status_use_case";
const DEFAULT_USER_STATUS_METRICS: UseCaseMetric[] = [
  { name: "cravings", description: "Urge intensity and frequency." },
  {
    name: "depression",
    description: "Low mood, hopelessness, and emotional heaviness.",
  },
  { name: "anxiety", description: "Stress, worry, and nervous system activation." },
  { name: "mood", description: "Overall emotional tone for the day." },
  { name: "energy", description: "Mental and physical energy availability." },
  { name: "focus", description: "Attention quality and ability to stay on task." },
];

type EditableMetric = {
  name: string;
  description: string;
};

const normalizeMetrics = (metrics: unknown): EditableMetric[] => {
  if (!Array.isArray(metrics)) {
    return DEFAULT_USER_STATUS_METRICS.map((metric) => ({
      name: metric.name,
      description: metric.description ?? "",
    }));
  }

  const deduped: EditableMetric[] = [];
  const seen = new Set<string>();
  for (const metric of metrics) {
    let name = "";
    let description = "";
    if (typeof metric === "string") {
      const cleaned = metric.trim();
      if (!cleaned) continue;
      if (cleaned.includes(":")) {
        const [namePart, descriptionPart] = cleaned.split(":", 2);
        name = namePart.trim();
        description = descriptionPart.trim();
      } else {
        name = cleaned;
      }
    } else if (metric && typeof metric === "object") {
      const nameCandidate =
        "name" in metric && typeof metric.name === "string"
          ? metric.name.trim()
          : "";
      const descriptionCandidate =
        "description" in metric && typeof metric.description === "string"
          ? metric.description.trim()
          : "";
      name = nameCandidate;
      description = descriptionCandidate;
    }

    if (!name) continue;
    const key = name.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push({ name, description });
  }

  return deduped.length
    ? deduped
    : DEFAULT_USER_STATUS_METRICS.map((metric) => ({
        name: metric.name,
        description: metric.description ?? "",
      }));
};

const UserStatusUseCaseCheckInConfigPage: Component = () => {
  const [config, { mutate }] = createResource(() =>
    usecaseConfigAPI.getConfigForUseCaseWithStatus(USER_STATUS_USECASE, {
      user_amendments: [],
      metrics: DEFAULT_USER_STATUS_METRICS.map((metric) => ({ ...metric })),
    }),
  );
  const [snapshotPreview, { refetch: refetchSnapshotPreview }] =
    createResource<LLMRunResultSnapshot | null>(() =>
      usecaseConfigAPI.getLLMSnapshotPreviewForUseCase(USER_STATUS_USECASE),
    );
  const [amendments, setAmendments] = createSignal<string[]>([]);
  const [metrics, setMetrics] = createSignal<EditableMetric[]>(
    DEFAULT_USER_STATUS_METRICS.map((metric) => ({
      name: metric.name,
      description: metric.description ?? "",
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
    setMetrics(normalizeMetrics(configData.config.metrics));
    setError("");
  });

  const addMetric = () => {
    setMetrics((current) => [...current, { name: "", description: "" }]);
  };

  const removeMetric = (index: number) => {
    setMetrics((current) => current.filter((_, idx) => idx !== index));
  };

  const updateMetric = (
    index: number,
    key: keyof EditableMetric,
    value: string,
  ) => {
    setMetrics((current) =>
      current.map((metric, idx) =>
        idx === index ? { ...metric, [key]: value } : metric,
      ),
    );
  };

  const sanitizedMetrics = () => normalizeMetrics(metrics()).map((metric) => ({
    name: metric.name,
    description: metric.description,
  }));

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      const wasConfigured = isConfigured();
      const updated = await usecaseConfigAPI.updateConfigForUseCase(
        USER_STATUS_USECASE,
        {
          user_amendments: amendments(),
          metrics: sanitizedMetrics(),
        },
      );
      mutate({ config: updated, exists: true });
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
            day context. Start by choosing the metrics you want scored, then
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
            <h2 class="text-lg font-semibold text-gray-900">Metrics to score</h2>
            <p class="text-sm text-gray-600">
              Define each metric as a name and description so the model knows
              exactly what to score from 0-100.
            </p>
          </div>
          <button
            type="button"
            onClick={addMetric}
            disabled={isSaving() || config.loading}
            class="px-3 py-2 rounded-md border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
          >
            + Add Metric
          </button>
        </div>

        <div class="space-y-3">
          <For each={metrics()}>
            {(metric, index) => (
              <div class="rounded-md border border-gray-200 p-3 bg-gray-50/40">
                <div class="grid grid-cols-1 md:grid-cols-[220px_1fr_auto] gap-3 items-start">
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">
                      Name
                    </label>
                    <input
                      type="text"
                      value={metric.name}
                      onInput={(event) =>
                        updateMetric(index(), "name", event.currentTarget.value)
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
                      value={metric.description}
                      onInput={(event) =>
                        updateMetric(
                          index(),
                          "description",
                          event.currentTarget.value,
                        )
                      }
                      placeholder="What this metric should represent"
                      disabled={isSaving() || config.loading}
                      class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                    />
                  </div>
                  <div class="pt-6">
                    <button
                      type="button"
                      onClick={() => removeMetric(index())}
                      disabled={isSaving() || config.loading || metrics().length <= 1}
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
