import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createMemo, createResource, createSignal } from "solid-js";

import RecurringEventSeriesForm from "@/components/recurring-events/Form";
import SettingsPage from "@/components/shared/SettingsPage";
import { calendarEntrySeriesAPI } from "@/utils/api";
import { CalendarEntrySeries } from "@/types/api";

const RecurringEventSeriesDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [isDirty, setIsDirty] = createSignal(false);

  const [series, { mutate }] = createResource<CalendarEntrySeries | undefined, string>(
    () => params.id,
    async (id) => calendarEntrySeriesAPI.get(id)
  );

  const serializeSeries = (value: Partial<CalendarEntrySeries>) =>
    JSON.stringify({
      name: (value.name ?? "").trim(),
      event_category: value.event_category ?? null,
    });

  const initialSignature = createMemo(() => {
    const current = series();
    if (!current) return null;
    return serializeSeries(current);
  });

  const handleFormChange = (value: Partial<CalendarEntrySeries>) => {
    const baseline = initialSignature();
    if (!baseline) return;
    setIsDirty(serializeSeries(value) !== baseline);
  };

  const handleUpdate = async (partialSeries: Partial<CalendarEntrySeries>) => {
    const current = series();
    if (!current?.id) return;

    setError("");
    setIsLoading(true);
    try {
      const updated = await calendarEntrySeriesAPI.update({
        ...current,
        ...partialSeries,
        id: current.id,
      });
      mutate(updated);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update recurring event series";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Show
      when={series()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <SettingsPage
          heading="Edit Recurring Event Series"
          bottomLink={{
            label: "Back to Recurring Events",
            url: "/me/settings/recurring-events",
          }}
        >
          <div class="space-y-6">
            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Recurring Event Series
                  </div>
                  <div class="text-lg font-semibold text-stone-800">
                    {current().name}
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
                    form="recurring-series-form"
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full bg-stone-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isLoading() ? "Saving..." : "Save changes"}
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate("/me/settings/recurring-events")}
                    class="w-full sm:w-auto rounded-full border border-stone-200 bg-white px-5 py-3 text-sm font-semibold text-stone-600 shadow-sm transition hover:border-stone-300 hover:text-stone-800"
                  >
                    Back
                  </button>
                </div>
              </div>
            </div>

            <RecurringEventSeriesForm
              formId="recurring-series-form"
              initialData={current()}
              onSubmit={handleUpdate}
              onChange={handleFormChange}
              isLoading={isLoading()}
              error={error()}
              showSubmitButton={false}
            />
          </div>
        </SettingsPage>
      )}
    </Show>
  );
};

export default RecurringEventSeriesDetailPage;


