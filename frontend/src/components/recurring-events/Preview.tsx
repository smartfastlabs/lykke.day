import { Component, Show } from "solid-js";

import { CalendarEntrySeries } from "@/types/api";

interface RecurringEventSeriesPreviewProps {
  series: CalendarEntrySeries;
}

const formatDateTime = (value?: string | null): string => {
  if (!value) return "Not set";
  const date = new Date(value);
  return isNaN(date.getTime()) ? value : date.toLocaleString();
};

const RecurringEventSeriesPreview: Component<RecurringEventSeriesPreviewProps> = (
  props
) => {
  return (
    <div class="flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-md space-y-6">
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Recurring Event Series</h2>
          <div class="space-y-3">
            <div>
              <label class="text-sm font-medium text-neutral-500">Name</label>
              <div class="mt-1 text-base text-neutral-900">{props.series.name}</div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Platform</label>
              <div class="mt-1 text-base text-neutral-900">
                {props.series.platform}
                {props.series.platform_id ? ` • ${props.series.platform_id}` : ""}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Calendar ID</label>
              <div class="mt-1 text-xs text-neutral-900 break-all">
                {props.series.calendar_id}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Frequency</label>
              <div class="mt-1 text-base text-neutral-900">
                {props.series.frequency}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Event Category</label>
              <div class="mt-1 text-base text-neutral-900">
                {props.series.event_category ?? "Not set"}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Starts At</label>
              <div class="mt-1 text-base text-neutral-900">
                {formatDateTime(props.series.starts_at)}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Ends At</label>
              <div class="mt-1 text-base text-neutral-900">
                {formatDateTime(props.series.ends_at)}
              </div>
            </div>
            <Show when={props.series.recurrence && props.series.recurrence?.length}>
              {(recurrence) => (
                <div>
                  <label class="text-sm font-medium text-neutral-500">Recurrence</label>
                  <div class="mt-1 text-xs text-neutral-900 break-words">
                    {recurrence()?.join(", ")}
                  </div>
                </div>
              )}
            </Show>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecurringEventSeriesPreview;


