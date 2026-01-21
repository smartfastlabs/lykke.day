import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import DetailPage from "@/components/shared/DetailPage";
import DayTemplateForm from "@/components/day-templates/Form";
import DayTemplatePreview from "@/components/day-templates/Preview";
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

  const handleAddTimeBlock = async (
    timeBlockDefinitionId: string,
    startTime: string,
    endTime: string
  ) => {
    const current = dayTemplate();
    if (!current?.id) return;

    setIsRoutineLoading(true);
    setActionError("");
    try {
      const updated = await dayTemplateAPI.addTimeBlock(
        current.id,
        timeBlockDefinitionId,
        startTime,
        endTime
      );
      mutateDayTemplate(updated);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to add time block";
      setActionError(message);
    } finally {
      setIsRoutineLoading(false);
    }
  };

  const handleRemoveTimeBlock = async (
    timeBlockDefinitionId: string,
    startTime: string
  ) => {
    const current = dayTemplate();
    if (!current?.id) return;

    setIsRoutineLoading(true);
    setActionError("");
    try {
      const updated = await dayTemplateAPI.removeTimeBlock(
        current.id,
        timeBlockDefinitionId,
        startTime
      );
      mutateDayTemplate(updated);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to remove time block";
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
            <div class="flex flex-col items-center justify-center px-6 py-8">
              <div class="w-full max-w-3xl">
                <DayTemplatePreview
                  dayTemplate={current()}
                  routines={routines()}
                  onAddRoutine={handleAddRoutine}
                  onRemoveRoutine={handleRemoveRoutine}
                  onAddTimeBlock={handleAddTimeBlock}
                  onRemoveTimeBlock={handleRemoveTimeBlock}
                  isEditMode={false}
                  isLoading={isRoutineLoading()}
                  error={actionError()}
                />
              </div>
            </div>
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
                  onAddTimeBlock={handleAddTimeBlock}
                  onRemoveTimeBlock={handleRemoveTimeBlock}
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
