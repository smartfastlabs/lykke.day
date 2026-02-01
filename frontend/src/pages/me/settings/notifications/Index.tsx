import {
  Component,
  Show,
  createResource,
  createSignal,
  createEffect,
} from "solid-js";
import { useNavigate } from "@solidjs/router";
import SettingsPage from "@/components/shared/SettingsPage";
import AmendmentsEditor from "@/components/shared/AmendmentsEditor";
import LLMSnapshotDetails from "@/components/llm/LLMSnapshotDetails";
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
    <SettingsPage
      heading="Notification Settings"
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

        <AmendmentsEditor
          heading="User Customizations"
          description={
            "Add custom instructions that will be appended to the default notification prompt. These instructions override the default behavior."
          }
          amendments={amendments()}
          onChange={setAmendments}
          placeholder="Enter a new customization instruction..."
        />

        <div class="rounded-2xl border border-emerald-100/80 bg-white/80 p-5 shadow-sm shadow-emerald-900/5 space-y-4">
          <div>
            <h2 class="text-lg font-semibold mb-2">LLM Request Payload</h2>
            <p class="text-sm text-gray-600">
              Preview the exact payload that would be sent to the LLM provider.
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
                  provider to see the request payload.
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

export default NotificationConfigPage;
