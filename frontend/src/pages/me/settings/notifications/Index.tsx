import {
  Component,
  createResource,
  createSignal,
  createEffect,
} from "solid-js";
import { useNavigate } from "@solidjs/router";
import UseCaseConfigPageLayout from "@/components/settings/UseCaseConfigPageLayout";
import { usecaseConfigAPI } from "@/utils/api";
import type {
  LLMRunResultSnapshot,
  NotificationUseCaseConfig,
} from "@/types/api";
import { globalNotifications } from "@/providers/notifications";

const NotificationConfigPage: Component = () => {
  const navigate = useNavigate();
  const [config, { mutate }] = createResource<NotificationUseCaseConfig>(
    usecaseConfigAPI.getNotificationConfig,
  );
  const [snapshotPreview, { refetch: refetchSnapshotPreview }] =
    createResource<LLMRunResultSnapshot | null>(
      usecaseConfigAPI.getNotificationLLMSnapshotPreview,
    );
  const [amendments, setAmendments] = createSignal<string[]>([]);
  const [isSaving, setIsSaving] = createSignal(false);
  const [error, setError] = createSignal<string>("");

  // Initialize amendments when config loads or changes
  createEffect(() => {
    const configData = config();
    if (configData) {
      setAmendments([...configData.user_amendments]);
      setError("");
    } else if (!config.loading && config.error) {
      // Only set error if it's not a 404 (which is handled by the API)
      const err = config.error;
      if (err instanceof Error && !err.message.includes("404")) {
        setError(err.message);
      }
    }
  });

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      // Save notification config amendments
      const updated = await usecaseConfigAPI.updateNotificationConfig({
        user_amendments: amendments(),
      });
      // Update the resource directly to avoid refetch delay
      mutate(updated);
      refetchSnapshotPreview();

      globalNotifications.addSuccess(
        "Notification settings saved successfully",
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
      heading="Notification Settings"
      error={error()}
      isLoading={config.loading}
      isSaving={isSaving()}
      amendments={amendments()}
      onAmendmentsChange={setAmendments}
      onSave={handleSave}
      snapshotPreview={snapshotPreview()}
      snapshotLoading={snapshotPreview.loading}
      amendmentsDescription="Add custom instructions that will be appended to the default notification prompt. These instructions override the default behavior."
    >
      {/* Navigation to Push Subscriptions */}
      <div class="mb-6">
        <button
          type="button"
          onClick={() => navigate("/me/settings/notifications/push")}
          class="w-full px-4 py-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
        >
          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-gray-900">Push Subscriptions</div>
              <div class="text-sm text-gray-500">
                Manage your push notification devices
              </div>
            </div>
            <div class="text-gray-400">→</div>
          </div>
        </button>
      </div>
    </UseCaseConfigPageLayout>
  );
};

export default NotificationConfigPage;
