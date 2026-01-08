import { Component, For, Show } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import type { Accessor } from "solid-js";
import { getTypeIcon } from "@/utils/icons";
import { Event } from "@/types/api";

const formatDateTime = (dateTimeStr: string): string => {
  const date = new Date(dateTimeStr);
  return date
    .toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    .toLowerCase()
    .replace(" ", "");
};

const isAllDayEvent = (event: Event): boolean => {
  const start = new Date(event.starts_at);
  const end = event.ends_at ? new Date(event.ends_at) : null;
  if (!end) return false;
  const diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
  return diffHours >= 23;
};

const AllDayEventItem: Component<{ event: Event }> = (props) => {
  const icon = () => getTypeIcon("EVENT");

  return (
    <div class="group px-5 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer">
      <div class="flex items-center gap-4">
        <div class="w-14 flex-shrink-0 text-right">
          <span class="text-xs text-gray-400">all day</span>
        </div>
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <span class="w-4 flex-shrink-0 flex items-center justify-center">
            <Show when={icon()}>
              <Icon icon={icon()!} />
            </Show>
          </span>
          <span class="text-sm text-gray-700 truncate">{props.event.name}</span>
        </div>
      </div>
    </div>
  );
};

const TimedEventItem: Component<{ event: Event }> = (props) => {
  const icon = () => getTypeIcon("EVENT");

  return (
    <div class="group px-5 py-3.5 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer">
      <div class="flex items-center gap-4">
        <div class="w-14 flex-shrink-0 text-right">
          <span class="text-xs tabular-nums text-gray-500">
            {formatDateTime(props.event.starts_at)}
          </span>
        </div>
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <span class="w-4 flex-shrink-0 flex items-center justify-center">
            <Show when={icon()}>
              <Icon icon={icon()!} />
            </Show>
          </span>
          <span class="text-sm font-medium text-gray-800 truncate">
            {props.event.name}
          </span>
        </div>
        <Show when={props.event.people?.length}>
          <span class="text-xs text-gray-400 truncate max-w-24">
            {props.event.people!.map((p) => p.name).join(", ")}
          </span>
        </Show>
      </div>
    </div>
  );
};

const sortEvents = (events: Event[]): Event[] => {
  return [...events].sort((a, b) => {
    const aTime = new Date(a.starts_at).getTime();
    const bTime = new Date(b.starts_at).getTime();
    return aTime - bTime;
  });
};

interface EventListProps {
  events: Accessor<Event[]>;
}

const EventList: Component<EventListProps> = (props) => {
  const allDayEvents = () =>
    sortEvents(props.events()?.filter(isAllDayEvent) ?? []);
  const timedEvents = () =>
    sortEvents(props.events()?.filter((e) => !isAllDayEvent(e)) ?? []);

  return (
    <>
      <For each={allDayEvents()}>
        {(event) => <AllDayEventItem event={event} />}
      </For>
      <For each={timedEvents()}>
        {(event) => <TimedEventItem event={event} />}
      </For>
    </>
  );
};

export default EventList;
