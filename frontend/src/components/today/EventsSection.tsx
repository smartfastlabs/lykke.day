import { Component, For, Show, createMemo } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faBars, faCalendarDay } from "@fortawesome/free-solid-svg-icons";
import type { Event } from "@/types/api";
import { EventItem } from "@/components/events/EventItem";

export interface EventsSectionProps {
  events: Event[];
  href: string;
}

export const EventsSection: Component<EventsSectionProps> = (props) => {
  const importantEvents = createMemo(() => {
    const now = new Date();
    return props.events
      .filter((e) => new Date(e.starts_at) >= now && e.category === "WORK")
      .sort(
        (a, b) =>
          new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime()
      )
      .slice(0, 3);
  });

  return (
    <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <Icon icon={faCalendarDay} class="w-5 h-5 fill-amber-600" />
          <p class="text-xs uppercase tracking-wide text-amber-700">Events</p>
        </div>
        <a
          class="inline-flex items-center justify-center w-9 h-9 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-600/80 transition hover:bg-amber-100/80 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200"
          href={props.href}
          aria-label="See all events"
          title="See all events"
        >
          <Icon icon={faBars} class="w-4 h-4 fill-amber-600/80" />
        </a>
      </div>
      <Show when={importantEvents().length > 0}>
        <For each={importantEvents()}>
          {(event) => <EventItem event={event} />}
        </For>
      </Show>
    </div>
  );
};
