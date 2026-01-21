import { Component, For, Show, createMemo } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faCalendarDay } from "@fortawesome/free-solid-svg-icons";
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

  const otherCount = createMemo(() => {
    const now = new Date();
    const importantIds = new Set(importantEvents().map((e) => e.id));
    return props.events.filter(
      (e) =>
        new Date(e.starts_at) >= now &&
        !importantIds.has(e.id) &&
        e.category !== "WORK"
    ).length;
  });

  return (
    <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <Icon icon={faCalendarDay} class="w-5 h-5 fill-amber-600" />
          <p class="text-xs uppercase tracking-wide text-amber-700">Events</p>
        </div>
        <a
          class="text-xs font-semibold text-amber-700 hover:text-amber-800"
          href={props.href}
        >
          See all events
        </a>
      </div>
      <Show when={importantEvents().length > 0}>
        <For each={importantEvents()}>
          {(event) => <EventItem event={event} />}
        </For>
      </Show>
      <Show when={otherCount() > 0}>
        <p class="text-xs text-stone-500">
          {otherCount()} other event{otherCount() !== 1 ? "s" : ""}
        </p>
      </Show>
      <Show when={importantEvents().length === 0 && otherCount() === 0}>
        <p class="text-xs text-stone-500">No events</p>
      </Show>
    </div>
  );
};
