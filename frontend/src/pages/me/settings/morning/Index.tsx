import {
  Component,
  createEffect,
  createResource,
  createSignal,
} from "solid-js";
import UseCaseConfigPageLayout from "@/components/settings/UseCaseConfigPageLayout";
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
  const normalizeTimeValue = (value: string | null | undefined) =>
    value ? value.slice(0, 5) : "";

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
      setMorningOverviewTime(
        normalizeTimeValue(currentUser.settings.morning_overview_time),
      );
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

      const timeValue =
        normalizeTimeValue(morningOverviewTime().trim()) || null;
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
    <UseCaseConfigPageLayout
      heading="Morning Overview Settings"
      error={error()}
      isLoading={config.loading}
      isSaving={isSaving()}
      amendments={amendments()}
      onAmendmentsChange={setAmendments}
      onSave={handleSave}
      snapshotPreview={snapshotPreview()}
      snapshotLoading={snapshotPreview.loading}
      amendmentsDescription="Add custom instructions that will be appended to the default morning overview prompt."
    >
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
    </UseCaseConfigPageLayout>
  );
};

export default MorningOverviewConfigPage;
