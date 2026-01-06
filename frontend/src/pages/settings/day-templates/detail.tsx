import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import Page from "../../../components/shared/layout/page";
import DayTemplateForm from "../../../components/dayTemplates/form";
import { dayTemplateAPI } from "../../../utils/api";
import { DayTemplate } from "../../../types/api";

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

  return (
    <Page>
      <Show
        when={dayTemplate()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        {(current) => (
          <div class="min-h-screen bg-neutral-50 flex flex-col items-center justify-center px-6">
            <div class="w-full max-w-sm space-y-6">
              <div class="flex items-center justify-between">
                <h1 class="text-2xl font-medium text-neutral-900">
                  Edit Day Template
                </h1>
                <button
                  type="button"
                  class="text-sm text-red-600 hover:text-red-700"
                  onClick={handleDelete}
                  disabled={isLoading()}
                >
                  Delete
                </button>
              </div>

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
    </Page>
  );
};

export default DayTemplateDetailPage;

