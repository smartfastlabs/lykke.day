import {
  Component,
  Show,
  createEffect,
  createResource,
  createSignal,
} from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import AmendmentsEditor from "@/components/shared/AmendmentsEditor";
import LLMSnapshotDetails from "@/components/llm/LLMSnapshotDetails";
import { Input } from "@/components/forms";
import { useAuth } from "@/providers/auth";
import { usecaseConfigAPI, authAPI } from "@/utils/api";
import { globalNotifications } from "@/providers/notifications";
import type {
  LLMRunResultSnapshot,
  NotificationUseCaseConfig,
} from "@/types/api";

const MorningOverviewConfigPage: Component = () => {
  const { user, refetch: refetchUser } = useAuth();
  const [config, { mutate }] = createResource<NotificationUseCaseConfig>(
    usecaseConfigAPI.getMorningOverviewConfig,
  );
  const [snapshotPreview, { refetch: refetchSnapshotPreview }] =
    createResource<LLMRunResultSnapshot | null>(
      usecaseConfigAPI.getMorningOverviewLLMSnapshotPreview,
    );
  const [amendments, setAmendments] = createSignal<string[]>([]);
  const [morningOverviewTime, setMorningOverviewTime] =
    createSignal<string>("");
  const [isSaving, setIsSaving] = createSignal(false);
  const [error, setError] = createSignal<string>("");

  createEffect(() => {
    const configData = config();
    if (configData) {
      setAmendments([...configData.user_amendments]);
      setError("");
    } else if (!config.loading && config.error) {
      const err = config.error;
      if (err instanceof Error && !err.message.includes("404")) {
        setError(err.message);
      }
    }
  });

  createEffect(() => {
    const currentUser = user();
    if (currentUser?.settings.morning_overview_time) {
      setMorningOverviewTime(currentUser.settings.morning_overview_time);
    } else {
      setMorningOverviewTime("");
    }
  });

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      const updated = await usecaseConfigAPI.updateMorningOverviewConfig({
        user_amendments: amendments(),
      });
      mutate(updated);

      const timeValue = morningOverviewTime().trim() || null;
      if (user()) {
        await authAPI.updateProfile({
          settings: {
            morning_overview_time: timeValue,
          },
        });
        await refetchUser();
      }

      refetchSnapshotPreview();
      globalNotifications.addSuccess(
        "Morning overview settings saved successfully",
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

  return (
    <SettingsPage
      heading="Morning Overview Settings"
      bottomLink={{ label: "Back to Settings", url: "/me/settings" }}
    >
      <div class="space-y-6">
        <Show when={error()}>
          <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error()}
          </div>
        </Show>

        <Show when={config.loading}>
          <div class="text-center text-gray-500 py-8">Loading...</div>
        </Show>

        <div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div class="mb-4">
            <h2 class="text-lg font-semibold text-gray-900 mb-1">
              Morning Overview
            </h2>
            <p class="text-sm text-gray-600">
              Set a time to receive a daily morning overview notification
              highlighting out-of-the-ordinary items and high-risk tasks.
            </p>
          </div>
          <div class="space-y-2">
            <label
              for="morning-overview-time"
              class="block text-sm font-medium text-gray-700"
            >
              Overview Time
            </label>
            <Input
              id="morning-overview-time"
              type="time"
              value={morningOverviewTime}
              onChange={setMorningOverviewTime}
              placeholder="07:30"
            />
            <p class="text-xs text-gray-500">
              Time in your local timezone (24-hour format). Leave empty to
              disable morning overviews.
            </p>
          </div>
        </div>

        <AmendmentsEditor
          heading="User Customizations"
          description="Add custom instructions that will be appended to the default morning overview prompt."
          amendments={amendments()}
          onChange={setAmendments}
          placeholder="Enter a new customization instruction..."
          disabled={isSaving() || config.loading}
        />

        <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-4">
          <div>
            <h2 class="text-lg font-semibold mb-2">Fully Rendered Prompt</h2>
            <p class="text-sm text-gray-600">
              This preview shows the full prompt, tools, and context that would
              be stored with a morning overview decision.
            </p>
          </div>
          <Show
            when={!snapshotPreview.loading}
            fallback={
              <div class="text-sm text-stone-500">Loading preview...</div>
            }
          >
            <Show
              when={snapshotPreview()}
              fallback={
                <div class="text-sm text-stone-500">
                  No LLM snapshot preview is available yet. Configure an LLM
                  provider to see the full prompt.
                </div>
              }
            >
              {(snapshot) => <LLMSnapshotDetails snapshot={snapshot()!} />}
            </Show>
          </Show>
        </div>

        <div class="flex justify-end gap-3 pt-4 border-t">
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving() || config.loading}
            class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving() ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>
    </SettingsPage>
  );
};

export default MorningOverviewConfigPage;
