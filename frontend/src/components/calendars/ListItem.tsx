import { Component, Show } from "solid-js";
import { Calendar } from "@/types/api";

interface CalendarListItemProps {
  calendar: Calendar;
}

const CalendarListItem: Component<CalendarListItemProps> = (props) => {
  const isSynced = () =>
    props.calendar.sync_enabled ?? Boolean(props.calendar.sync_subscription);

  return (
    <div class="flex items-center gap-4">
      <div class="flex-1 min-w-0">
        <span class="text-sm font-semibold text-stone-700 block truncate">
          {props.calendar.name}
        </span>
        <span class="text-xs text-stone-500">
          {props.calendar.platform}
          {props.calendar.platform_id ? ` • ${props.calendar.platform_id}` : ""}
        </span>
      </div>
      <span
        class={`text-[11px] px-2 py-1 rounded-full ${
          isSynced()
            ? "bg-emerald-50 text-emerald-700 border border-emerald-100"
            : "bg-stone-100 text-stone-500 border border-stone-200"
        }`}
      >
        {isSynced() ? "Sync On" : "Sync Off"}
      </span>
      <Show when={props.calendar.last_sync_at}>
        {(lastSync) => (
          <span class="text-[11px] text-stone-400 whitespace-nowrap">
            Synced {new Date(lastSync()).toLocaleDateString()}
          </span>
        )}
      </Show>
    </div>
  );
};

export default CalendarListItem;

