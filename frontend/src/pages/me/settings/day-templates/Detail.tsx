import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createMemo, createResource, createSignal } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import DayTemplateForm from "@/components/day-templates/Form";
import DayTemplatePreview from "@/components/day-templates/Preview";
import { dayTemplateAPI, routineDefinitionAPI } from "@/utils/api";
import { DayTemplate, RoutineDefinition } from "@/types/api";

const DayTemplateDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [actionError, setActionError] = createSignal("");
  const [isRoutineLoading, setIsRoutineLoading] = createSignal(false);
  const [isDirty, setIsDirty] = createSignal(false);

  const [dayTemplate, { mutate: mutateDayTemplate }] = createResource<
    DayTemplate | undefined,
    string
  >(
    () => params.id,
    async (id) => dayTemplateAPI.get(id)
  );

  const [routineDefinitions] = createResource<RoutineDefinition[]>(
    routineDefinitionAPI.getAll
  );

  const serializeDayTemplate = (value: Partial<DayTemplate>) =>
    JSON.stringify({
      slug: (value.slug ?? "").trim(),
      icon: (value.icon ?? "").trim(),
      start_time: value.start_time ?? null,
      end_time: value.end_time ?? null,
      alarms: value.alarms ?? [],
      high_level_plan: value.high_level_plan
        ? {
            title: (value.high_level_plan.title ?? "").trim(),
            text: (value.high_level_plan.text ?? "").trim(),
            intentions: value.high_level_plan.intentions ?? [],
          }
        : null,
    });

  const initialSignature = createMemo(() => {
    const current = dayTemplate();
    if (!current) return null;
    return serializeDayTemplate(current);
  });

  const handleFormChange = (value: Partial<DayTemplate>) => {
    const baseline = initialSignature();
    if (!baseline) return;
    setIsDirty(serializeDayTemplate(value) !== baseline);
  };

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

  const handleAddRoutineDefinition = async (
    routineDefinitionId: string
  ) => {
    const current = dayTemplate();
    if (!current?.id) return;

    setIsRoutineLoading(true);
    setActionError("");
    try {
      const updated = await dayTemplateAPI.addRoutineDefinition(
        current.id,
        routineDefinitionId
      );
      mutateDayTemplate(updated);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to add routine definition";
      setActionError(message);
    } finally {
      setIsRoutineLoading(false);
    }
  };

  const handleRemoveRoutineDefinition = async (
    routineDefinitionId: string
  ) => {
    const current = dayTemplate();
    if (!current?.id) return;

    setIsRoutineLoading(true);
    setActionError("");
    try {
      const updated = await dayTemplateAPI.removeRoutineDefinition(
        current.id,
        routineDefinitionId
      );
      mutateDayTemplate(updated);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to remove routine definition";
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
        <SettingsPage
          heading="Edit Day Template"
          bottomLink={{
            label: "Back to Day Templates",
            url: "/me/settings/day-templates",
          }}
        >
          <div class="space-y-6">
            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Day Template
                  </div>
                  <div class="text-lg font-semibold text-stone-800">
                    {current().slug}
                  </div>
                  <Show
                    when={isDirty()}
                    fallback={<div class="text-xs text-stone-400">All changes saved</div>}
                  >
                    <div class="inline-flex items-center gap-2 text-xs font-medium text-amber-700">
                      <span class="h-2 w-2 rounded-full bg-amber-500" />
                      Unsaved changes
                    </div>
                  </Show>
                </div>
                <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <button
                    type="submit"
                    form="day-template-form"
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full bg-stone-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isLoading() ? "Saving..." : "Save changes"}
                  </button>
                  <button
                    type="button"
                    onClick={handleDelete}
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full border border-stone-200 bg-white px-5 py-3 text-sm font-semibold text-stone-600 shadow-sm transition hover:border-stone-300 hover:text-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Delete template
                  </button>
                </div>
              </div>
            </div>

            <div class="grid gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
              <DayTemplateForm
                formId="day-template-form"
                initialData={current()}
                onSubmit={handleUpdate}
                onChange={handleFormChange}
                isLoading={isLoading()}
                error={error()}
                showSubmitButton={false}
              />
              <DayTemplatePreview
                dayTemplate={current()}
                routineDefinitions={routineDefinitions()}
                onAddRoutineDefinition={handleAddRoutineDefinition}
                onRemoveRoutineDefinition={handleRemoveRoutineDefinition}
                onAddTimeBlock={handleAddTimeBlock}
                onRemoveTimeBlock={handleRemoveTimeBlock}
                isEditMode={true}
                isLoading={isRoutineLoading()}
                error={actionError()}
              />
            </div>
          </div>
        </SettingsPage>
      )}
    </Show>
  );
};

export default DayTemplateDetailPage;
