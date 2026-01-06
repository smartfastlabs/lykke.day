import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import DetailPage from "@/components/shared/detailPage";
import DayTemplateForm from "@/components/dayTemplates/form";
import DayTemplatePreview from "@/components/dayTemplates/preview";
import { dayTemplateAPI, routineAPI } from "@/utils/api";
import { DayTemplate, Routine } from "@/types/api";

const DayTemplateDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [actionError, setActionError] = createSignal("");
  const [isRoutineLoading, setIsRoutineLoading] = createSignal(false);

  const [dayTemplate, { mutate: mutateDayTemplate }] = createResource<
    DayTemplate | undefined,
    string
  >(
    () => params.id,
    async (id) => dayTemplateAPI.get(id)
  );

  const [routines] = createResource<Routine[]>(routineAPI.getAll);

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
      navigate("/me/settings/day-templates");
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
      navigate("/me/settings/day-templates");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete day template";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddRoutine = async (routineId: string) => {
    const current = dayTemplate();
    if (!current?.id) return;

    setIsRoutineLoading(true);
    setActionError("");
    try {
      const updated = await dayTemplateAPI.addRoutine(current.id, routineId);
      mutateDayTemplate(updated);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to add routine";
      setActionError(message);
    } finally {
      setIsRoutineLoading(false);
    }
  };

  const handleRemoveRoutine = async (routineId: string) => {
    const current = dayTemplate();
    if (!current?.id) return;

    setIsRoutineLoading(true);
    setActionError("");
    try {
      const updated = await dayTemplateAPI.removeRoutine(current.id, routineId);
      mutateDayTemplate(updated);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to remove routine";
      setActionError(message);
    } finally {
      setIsRoutineLoading(false);
    }
  };

  return (
    <Show
      when={dayTemplate()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <DetailPage
          heading="Day Template"
          bottomLink={{
            label: "Back to Day Templates",
            url: "/me/settings/day-templates",
          }}
          preview={
            <DayTemplatePreview
              dayTemplate={current()}
              routines={routines()}
              onAddRoutine={handleAddRoutine}
              onRemoveRoutine={handleRemoveRoutine}
              isEditMode={false}
              isLoading={isRoutineLoading()}
              error={actionError()}
            />
          }
          edit={
            <div class="flex flex-col items-center justify-center px-6 py-8">
              <div class="w-full max-w-3xl space-y-8">
                <DayTemplateForm
                  initialData={current()}
                  onSubmit={handleUpdate}
                  isLoading={isLoading()}
                  error={error()}
                />
                <DayTemplatePreview
                  dayTemplate={current()}
                  routines={routines()}
                  onAddRoutine={handleAddRoutine}
                  onRemoveRoutine={handleRemoveRoutine}
                  isEditMode={true}
                  isLoading={isRoutineLoading()}
                  error={actionError()}
                />
              </div>
            </div>
          }
          onDelete={handleDelete}
        />
      )}
    </Show>
  );
};

export default DayTemplateDetailPage;
