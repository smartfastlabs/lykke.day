import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import SettingsPage, { ActionButton } from "@/components/shared/settingsPage";
import DayTemplateForm from "@/components/dayTemplates/form";
import { dayTemplateAPI } from "@/utils/api";
import { DayTemplate } from "@/types/api";

const DayTemplateDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const [dayTemplate] = createResource<DayTemplate | undefined, string>(
    () => params.id,
    async (id) => dayTemplateAPI.get(id)
  );

  const handleUpdate = async (partialTemplate: Partial<DayTemplate>) => {
    const current = dayTemplate();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await dayTemplateAPI.update({
        ...current,
        ...partialTemplate,
        id: current.id,
      });
      navigate("/settings/day-templates");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update day template";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = dayTemplate();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await dayTemplateAPI.delete(current.id);
      navigate("/settings/day-templates");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete day template";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const actionButtons: ActionButton[] = [
    {
      label: "Delete",
      onClick: handleDelete,
    },
  ];

  return (
    <SettingsPage
      heading="Edit Day Template"
      actionButtons={actionButtons}
      bottomLink={{ label: "Back to Day Templates", url: "/settings/day-templates" }}
    >
      <Show
        when={dayTemplate()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        {(current) => (
          <div class="flex flex-col items-center justify-center px-6">
            <div class="w-full max-w-sm space-y-6">
              <DayTemplateForm
                initialData={current()}
                onSubmit={handleUpdate}
                isLoading={isLoading()}
                error={error()}
              />
            </div>
          </div>
        )}
      </Show>
    </SettingsPage>
  );
};

export default DayTemplateDetailPage;

