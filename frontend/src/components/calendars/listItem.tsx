import { Component, Show } from "solid-js";
import { Calendar } from "@/types/api";

interface CalendarListItemProps {
  calendar: Calendar;
}

const CalendarListItem: Component<CalendarListItemProps> = (props) => {
  return (
    <div class="flex items-center gap-4">
      <div class="flex-1 min-w-0">
        <span class="text-sm text-gray-800 block truncate">{props.calendar.name}</span>
        <span class="text-xs text-gray-500">
          {props.calendar.platform}
          {props.calendar.platform_id ? ` • ${props.calendar.platform_id}` : ""}
        </span>
      </div>
      <Show when={props.calendar.last_sync_at}>
        {(lastSync) => (
          <span class="text-[11px] text-gray-400 whitespace-nowrap">
            Synced {new Date(lastSync()).toLocaleDateString()}
          </span>
        )}
      </Show>
    </div>
  );
};

export default CalendarListItem;

