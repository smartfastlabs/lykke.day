import { useNavigate, useParams } from "@solidjs/router";
import { Component, For, Show, createMemo, createResource, createSignal } from "solid-js";
import SettingsPage, { ActionButton } from "@/components/shared/settingsPage";
import DayTemplateForm from "@/components/dayTemplates/form";
import { Icon } from "@/components/shared/icon";
import { dayTemplateAPI, routineAPI } from "@/utils/api";
import { DayTemplate, Routine } from "@/types/api";

const DayTemplateDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [actionError, setActionError] = createSignal("");
  const [isEditMode, setIsEditMode] = createSignal(false);
  const [isRoutineLoading, setIsRoutineLoading] = createSignal(false);

  const [dayTemplate, { mutate: mutateDayTemplate }] = createResource<
    DayTemplate | undefined,
    string
  >(() => params.id, async (id) => dayTemplateAPI.get(id));

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

  const handleAddRoutine = async (routineId: string) => {
    const current = dayTemplate();
    if (!current?.id) return;

    setIsRoutineLoading(true);
    setActionError("");
    try {
      const updated = await dayTemplateAPI.addRoutine(current.id, routineId);
      mutateDayTemplate(updated);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to add routine";
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
      const message = err instanceof Error ? err.message : "Failed to remove routine";
      setActionError(message);
    } finally {
      setIsRoutineLoading(false);
    }
  };

  const attachedRoutineIds = createMemo(() => new Set(dayTemplate()?.routine_ids ?? []));

  const attachedRoutines = createMemo(() =>
    (routines() ?? []).filter((routine) => routine.id && attachedRoutineIds().has(routine.id))
  );

  const availableRoutines = createMemo(() =>
    (routines() ?? []).filter((routine) => !routine.id || !attachedRoutineIds().has(routine.id))
  );

  const getRoutineName = (routineId: string) =>
    routines()?.find((r) => r.id === routineId)?.name ?? routineId;

  const actionButtons = createMemo((): ActionButton[] => {
    return [
      {
        label: isEditMode() ? "Exit Edit Mode" : "Edit Mode",
        onClick: () => setIsEditMode((prev) => !prev),
      },
      {
        label: "Delete",
        onClick: handleDelete,
      },
    ];
  });

  return (
    <SettingsPage
      heading="Edit Day Template"
      actionButtons={actionButtons()}
      bottomLink={{ label: "Back to Day Templates", url: "/settings/day-templates" }}
    >
      <Show
        when={dayTemplate()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        {(current) => (
          <div class="flex flex-col items-center justify-center px-6 py-8">
            <div class="w-full max-w-3xl space-y-8">
              <DayTemplateForm
                initialData={current()}
                onSubmit={handleUpdate}
                isLoading={isLoading()}
                error={error()}
              />

              <div class="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm space-y-4">
                <div class="flex items-center justify-between">
                  <div>
                    <h2 class="text-lg font-medium text-neutral-900">Routines</h2>
                    <p class="text-sm text-neutral-500">
                      Manage routines attached to this day template.
                    </p>
                  </div>
                  <Show when={isEditMode()}>
                    <div class="flex items-center gap-2 text-sm text-neutral-500">
                      <Icon key="info" class="w-4 h-4" />
                      <span>Click a routine to remove</span>
                    </div>
                  </Show>
                </div>

                <Show
                  when={attachedRoutines().length > 0}
                  fallback={<div class="text-sm text-neutral-500">No routines attached yet.</div>}
                >
                  <div class="space-y-3">
                    <For each={attachedRoutines()}>
                      {(routine) => (
                        <div class="flex items-start justify-between rounded-md border border-neutral-200 px-3 py-2">
                          <div class="space-y-1">
                            <div class="text-sm font-medium text-neutral-900">
                              {routine.name}
                            </div>
                            <div class="text-xs text-neutral-500">
                              {routine.description || "No description"}
                            </div>
                          </div>
                          <Show when={isEditMode()}>
                            <button
                              class="text-sm text-red-600 hover:text-red-700"
                              onClick={() => routine.id && handleRemoveRoutine(routine.id)}
                              disabled={isRoutineLoading()}
                            >
                              Remove
                            </button>
                          </Show>
                        </div>
                      )}
                    </For>
                  </div>
                </Show>

                <Show when={isEditMode()}>
                  <div class="space-y-3">
                    <div class="text-sm font-medium text-neutral-900">Add routine</div>
                    <Show
                      when={availableRoutines().length > 0}
                      fallback={
                        <div class="text-sm text-neutral-500">All routines attached.</div>
                      }
                    >
                      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <For each={availableRoutines()}>
                          {(routine) => (
                            <button
                              class="flex items-center justify-between rounded-md border border-neutral-200 px-3 py-2 text-left hover:border-neutral-300 hover:bg-neutral-50"
                              onClick={() => routine.id && handleAddRoutine(routine.id)}
                              disabled={isRoutineLoading()}
                            >
                              <span class="text-sm text-neutral-800">{routine.name}</span>
                              <Icon key="plus" class="w-4 h-4 text-neutral-500" />
                            </button>
                          )}
                        </For>
                      </div>
                    </Show>
                  </div>
                </Show>

                <Show when={actionError()}>
                  <div class="text-sm text-red-600">{actionError()}</div>
                </Show>
              </div>
            </div>
          </div>
        )}
      </Show>
    </SettingsPage>
  );
};

export default DayTemplateDetailPage;

