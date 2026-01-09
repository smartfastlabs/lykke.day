import { Component, Show } from "solid-js";

import { CalendarEntrySeries } from "@/types/api";
import { formatRecurrenceInfo } from "@/components/recurring-events/recurrenceFormat";

interface RecurringEventSeriesListItemProps {
  series: CalendarEntrySeries;
}

const RecurringEventSeriesListItem: Component<RecurringEventSeriesListItemProps> = (
  props
) => {
  const occurrence = formatRecurrenceInfo(props.series);
  return (
    <div class="flex items-center gap-4">
      <div class="flex-1 min-w-0">
        <span class="text-sm text-gray-800 block truncate">{props.series.name}</span>
        <span class="text-xs text-gray-500">
          {props.series.platform}
          {occurrence ? ` • ${occurrence}` : ""}
        </span>
      </div>
      <span class="text-[11px] px-2 py-1 rounded-full bg-gray-100 text-gray-600">
        {props.series.event_category ?? "Uncategorized"}
      </span>
      <Show when={props.series.frequency}>
        {(frequency) => (
          <span class="text-[11px] text-gray-400 whitespace-nowrap">
            {frequency()}
          </span>
        )}
      </Show>
    </div>
  );
};

export default RecurringEventSeriesListItem;


