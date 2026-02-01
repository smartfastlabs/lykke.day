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
import { usecaseConfigAPI } from "@/utils/api";
import { globalNotifications } from "@/providers/notifications";
import type { LLMRunResultSnapshot, MessagingUseCaseConfig } from "@/types/api";

const MessagingConfigPage: Component = () => {
  const [config, { mutate }] = createResource<MessagingUseCaseConfig>(
    usecaseConfigAPI.getMessagingConfig,
  );
  const [snapshotPreview, { refetch: refetchSnapshotPreview }] =
    createResource<LLMRunResultSnapshot | null>(
      usecaseConfigAPI.getMessagingLLMSnapshotPreview,
    );
  const [amendments, setAmendments] = createSignal<string[]>([]);
  const [sendAcknowledgment, setSendAcknowledgment] = createSignal(true);
  const [isSaving, setIsSaving] = createSignal(false);
  const [error, setError] = createSignal<string>("");

  createEffect(() => {
    const configData = config();
    if (configData) {
      setAmendments([...configData.user_amendments]);
      setSendAcknowledgment(configData.send_acknowledgment ?? true);
      setError("");
    } else if (!config.loading && config.error) {
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
      const updated = await usecaseConfigAPI.updateMessagingConfig({
        user_amendments: amendments(),
        send_acknowledgment: sendAcknowledgment(),
      });
      mutate(updated);
      refetchSnapshotPreview();
      globalNotifications.addSuccess("Messaging settings saved successfully");
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
      heading="Messaging Settings"
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

        <div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm space-y-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">
              Acknowledgment replies
            </h2>
            <p class="text-sm text-gray-600">
              Control whether Lykke sends a brief SMS confirmation when it takes
              action on your inbound messages.
            </p>
          </div>

          <label class="flex items-center gap-3 rounded-md border border-gray-200 px-3 py-2">
            <input
              type="checkbox"
              checked={sendAcknowledgment()}
              onChange={(event) =>
                setSendAcknowledgment(event.currentTarget.checked)
              }
              class="h-4 w-4 rounded border-neutral-300 text-stone-900 focus:ring-amber-300"
              disabled={isSaving() || config.loading}
            />
            <span class="text-sm text-neutral-800">Send acknowledgment</span>
          </label>

          <p class="text-xs text-gray-500">
            When disabled, actions are still taken but no confirmation message is
            sent.
          </p>
        </div>

        <AmendmentsEditor
          heading="User Customizations"
          description="Add custom instructions that will be appended to the default messaging prompt."
          amendments={amendments()}
          onChange={setAmendments}
          placeholder="Enter a new customization instruction..."
          disabled={isSaving() || config.loading}
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

export default MessagingConfigPage;
