import { Component, For, Show, createResource, createSignal, createEffect } from "solid-js";
import { useNavigate } from "@solidjs/router";
import SettingsPage from "@/components/shared/SettingsPage";
import { usecaseConfigAPI } from "@/utils/api";
import type { NotificationUseCaseConfig } from "@/types/api";
import { globalNotifications } from "@/providers/notifications";

const NotificationConfigPage: Component = () => {
  const navigate = useNavigate();
  const [config, { refetch, mutate }] = createResource<NotificationUseCaseConfig>(
    usecaseConfigAPI.getNotificationConfig
  );
  const [amendments, setAmendments] = createSignal<string[]>([]);
  const [isSaving, setIsSaving] = createSignal(false);
  const [newAmendment, setNewAmendment] = createSignal("");
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

  const handleAddAmendment = () => {
    const text = newAmendment().trim();
    if (text) {
      setAmendments([...amendments(), text]);
      setNewAmendment("");
    }
  };

  const handleRemoveAmendment = (index: number) => {
    setAmendments(amendments().filter((_, i) => i !== index));
  };

  const handleUpdateAmendment = (index: number, value: string) => {
    const updated = [...amendments()];
    updated[index] = value;
    setAmendments(updated);
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      const updated = await usecaseConfigAPI.updateNotificationConfig({
        user_amendments: amendments(),
      });
      // Update the resource directly to avoid refetch delay
      mutate(updated);
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
        
        <div>
          <h2 class="text-lg font-semibold mb-2">User Customizations</h2>
          <p class="text-sm text-gray-600 mb-4">
            Add custom instructions that will be appended to the default notification prompt.
            These instructions override the default behavior.
          </p>
          
          <div class="space-y-3">
            <For each={amendments()}>
              {(amendment, index) => (
                <div class="flex gap-2 items-start">
                  <textarea
                    value={amendment}
                    onInput={(e) => handleUpdateAmendment(index(), e.currentTarget.value)}
                    class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={2}
                  />
                  <button
                    type="button"
                    onClick={() => handleRemoveAmendment(index())}
                    class="px-3 py-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                  >
                    Remove
                  </button>
                </div>
              )}
            </For>
            
            <div class="flex gap-2">
              <textarea
                value={newAmendment()}
                onInput={(e) => setNewAmendment(e.currentTarget.value)}
                placeholder="Enter a new customization instruction..."
                class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={2}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    handleAddAmendment();
                  }
                }}
              />
              <button
                type="button"
                onClick={handleAddAmendment}
                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Add
              </button>
            </div>
          </div>
        </div>

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
