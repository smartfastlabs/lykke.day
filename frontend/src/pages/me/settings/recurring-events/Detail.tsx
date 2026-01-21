import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";

import RecurringEventSeriesForm from "@/components/recurring-events/Form";
import RecurringEventSeriesPreview from "@/components/recurring-events/Preview";
import DetailPage from "@/components/shared/DetailPage";
import { calendarEntrySeriesAPI } from "@/utils/api";
import { CalendarEntrySeries } from "@/types/api";

const RecurringEventSeriesDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const [series, { mutate }] = createResource<CalendarEntrySeries | undefined, string>(
    () => params.id,
    async (id) => calendarEntrySeriesAPI.get(id)
  );

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
        <DetailPage
          heading="Recurring Event Series"
          bottomLink={{
            label: "Back to Recurring Events",
            url: "/me/settings/recurring-events",
          }}
          preview={<RecurringEventSeriesPreview series={current()} />}
          edit={
            <div class="flex flex-col items-center justify-center px-6 py-8">
              <div class="w-full max-w-sm space-y-6">
                <RecurringEventSeriesForm
                  initialData={current()}
                  onSubmit={handleUpdate}
                  isLoading={isLoading()}
                  error={error()}
                />
              </div>
            </div>
          }
          additionalActionButtons={[
            {
              label: "Back",
              onClick: () => navigate("/me/settings/recurring-events"),
            },
          ]}
        />
      )}
    </Show>
  );
};

export default RecurringEventSeriesDetailPage;


