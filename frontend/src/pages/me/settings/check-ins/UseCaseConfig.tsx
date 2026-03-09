import { Component, createEffect, createResource, createSignal } from "solid-js";
import UseCaseConfigPageLayout from "@/components/settings/UseCaseConfigPageLayout";
import { globalNotifications } from "@/providers/notifications";
import type { LLMRunResultSnapshot, NotificationUseCaseConfig } from "@/types/api";
import { usecaseConfigAPI } from "@/utils/api";

interface CheckInUseCaseConfigPageProps {
  heading: string;
  usecase: string;
  successMessage: string;
  amendmentsDescription: string;
}

const CheckInUseCaseConfigPage: Component<CheckInUseCaseConfigPageProps> = (
  props,
) => {
  const [config, { mutate }] = createResource<NotificationUseCaseConfig>(() =>
    usecaseConfigAPI.getConfigForUseCase(props.usecase),
  );
  const [snapshotPreview, { refetch: refetchSnapshotPreview }] =
    createResource<LLMRunResultSnapshot | null>(() =>
      usecaseConfigAPI.getLLMSnapshotPreviewForUseCase(props.usecase),
    );
  const [amendments, setAmendments] = createSignal<string[]>([]);
  const [isSaving, setIsSaving] = createSignal(false);
  const [error, setError] = createSignal("");

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

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      const updated = await usecaseConfigAPI.updateConfigForUseCase(props.usecase, {
        user_amendments: amendments(),
      });
      mutate(updated);
      await refetchSnapshotPreview();
      globalNotifications.addSuccess(props.successMessage);
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
      heading={props.heading}
      error={error()}
      isLoading={config.loading}
      isSaving={isSaving()}
      amendments={amendments()}
      onAmendmentsChange={setAmendments}
      onSave={handleSave}
      snapshotPreview={snapshotPreview()}
      snapshotLoading={snapshotPreview.loading}
      amendmentsDescription={props.amendmentsDescription}
    />
  );
};

export default CheckInUseCaseConfigPage;
