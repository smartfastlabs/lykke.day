import { Component, Show, createResource, createSignal, createEffect } from "solid-js";
import { useNavigate } from "@solidjs/router";
import SettingsPage from "@/components/shared/SettingsPage";
import AmendmentsEditor from "@/components/shared/AmendmentsEditor";
import { Input } from "@/components/forms";
import { useAuth } from "@/providers/auth";
import { usecaseConfigAPI, authAPI } from "@/utils/api";
import type { NotificationUseCaseConfig } from "@/types/api";
import { globalNotifications } from "@/providers/notifications";

const NotificationConfigPage: Component = () => {
  const navigate = useNavigate();
  const { user, refetch: refetchUser } = useAuth();
  const [config, { mutate }] = createResource<NotificationUseCaseConfig>(
    usecaseConfigAPI.getNotificationConfig
  );
  const [amendments, setAmendments] = createSignal<string[]>([]);
  const [morningOverviewTime, setMorningOverviewTime] = createSignal<string>("");
  const [isSaving, setIsSaving] = createSignal(false);
  const [error, setError] = createSignal<string>("");

  // Initialize amendments and morning overview time when config/user loads or changes
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
      // Save notification config amendments
      const updated = await usecaseConfigAPI.updateNotificationConfig({
        user_amendments: amendments(),
      });
      // Update the resource directly to avoid refetch delay
      mutate(updated);
      
      // Save morning overview time to user profile
      const timeValue = morningOverviewTime().trim() || null;
      if (user()) {
        await authAPI.updateProfile({
          settings: {
            morning_overview_time: timeValue,
          },
        });
        await refetchUser();
      }
      
      globalNotifications.addSuccess("Notification settings saved successfully");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to save settings";
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
                <div class="text-sm text-gray-500">Manage your push notification devices</div>
              </div>
              <div class="text-gray-400">→</div>
            </div>
          </button>
        </div>
        
        {/* Morning Overview Time Setting */}
        <div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div class="mb-4">
            <h2 class="text-lg font-semibold text-gray-900 mb-1">Morning Overview</h2>
            <p class="text-sm text-gray-600">
              Set a time to receive a daily morning overview notification highlighting out-of-the-ordinary items and high-risk tasks.
            </p>
          </div>
          <div class="space-y-2">
            <label for="morning-overview-time" class="block text-sm font-medium text-gray-700">
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
              Time in your local timezone (24-hour format). Leave empty to disable morning overviews.
            </p>
          </div>
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

        <Show when={config()?.rendered_prompt}>
          <div>
            <h2 class="text-lg font-semibold mb-2">Fully Rendered Prompt</h2>
            <p class="text-sm text-gray-600 mb-4">
              This is what the AI sees when evaluating notifications for you.
            </p>
            <div class="bg-gray-50 border border-gray-200 rounded-md p-4 overflow-auto">
              <pre class="text-sm text-gray-800 whitespace-pre-wrap font-mono">{config()?.rendered_prompt}</pre>
            </div>
          </div>
        </Show>

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
