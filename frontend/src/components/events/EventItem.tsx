import { Component, Show } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import type { Event } from "@/types/api";
import { getTypeIcon } from "@/utils/icons";
import { formatByFrequency } from "@/components/recurring-events/recurrenceFormat";

export interface EventItemProps {
  event: Event;
}

const formatDateTime = (dateTimeStr: string): string => {
  const date = new Date(dateTimeStr);
  return date
    .toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    .toLowerCase()
    .replace(" ", "");
};

const formatCategory = (category?: Event["category"]): string =>
  (category ?? "OTHER").toLowerCase().replace("_", " ");

export const EventItem: Component<EventItemProps> = (props) => {
  const icon = () => getTypeIcon("EVENT");
  const categoryLabel = () => formatCategory(props.event.category);
  const frequencyLabel = () => formatByFrequency(props.event.frequency);

  return (
    <div class="flex items-start gap-3">
      <div class="mt-0.5">
        <Show when={icon()}>
          <Icon icon={icon()!} class="w-4 h-4" />
        </Show>
      </div>
      <div class="flex-1">
        <p class="text-sm font-semibold text-stone-800">{props.event.name}</p>
        <div class="flex items-center gap-2 mt-1">
          <p class="text-xs text-stone-500">{formatDateTime(props.event.starts_at)}</p>
          <span class="text-[10px] font-medium uppercase tracking-wide text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">
            {categoryLabel()}
          </span>
          <span class="text-[10px] font-medium uppercase tracking-wide text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">
            {frequencyLabel()}
          </span>
        </div>
      </div>
    </div>
  );
};
