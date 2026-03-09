import {
  Component,
  createEffect,
  createResource,
  createSignal,
} from "solid-js";
import UseCaseConfigPageLayout from "@/components/settings/UseCaseConfigPageLayout";
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
    <UseCaseConfigPageLayout
      heading="Messaging Settings"
      error={error()}
      isLoading={config.loading}
      isSaving={isSaving()}
      amendments={amendments()}
      onAmendmentsChange={setAmendments}
      onSave={handleSave}
      snapshotPreview={snapshotPreview()}
      snapshotLoading={snapshotPreview.loading}
      amendmentsDescription="Add custom instructions that will be appended to the default messaging prompt."
    >
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
    </UseCaseConfigPageLayout>
  );
};

export default MessagingConfigPage;
