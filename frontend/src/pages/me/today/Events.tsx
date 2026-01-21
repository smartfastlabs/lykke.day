import { Component, createMemo, For, Show } from "solid-js";
import { useStreamingData } from "@/providers/streamingData";
import type { Event } from "@/types/api";
import { Icon } from "solid-heroicons";
import { calendar } from "solid-heroicons/outline";
import { usePageAnimation } from "@/utils/navigation";
import { EventItem } from "@/components/events/EventItem";

const EmptyState: Component = () => (
  <div class="text-center py-16">
    <div class="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center">
      <Icon path={calendar} class="w-10 h-10 text-amber-700" />
    </div>
    <h3 class="text-xl font-semibold text-stone-800 mb-2">No events today</h3>
    <p class="text-stone-600">Enjoy your free time!</p>
  </div>
);

export const TodaysEventsView: Component = () => {
  const { events } = useStreamingData();
  const mounted = usePageAnimation("today-events");

  const now = createMemo(() => new Date());

  const upcomingEvents = createMemo(() => {
    const allEvents = events() ?? [];
    return allEvents
      .filter((event) => new Date(event.starts_at) >= now())
      .sort(
        (a, b) =>
          new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime()
      );
  });

  const pastEvents = createMemo(() => {
    const allEvents = events() ?? [];
    return allEvents
      .filter((event) => new Date(event.starts_at) < now())
      .sort(
        (a, b) =>
          new Date(b.starts_at).getTime() - new Date(a.starts_at).getTime()
      );
  });

  const totalEvents = createMemo(
    () => upcomingEvents().length + pastEvents().length
  );

  return (
    <div class="w-full">
      {/* Summary section */}
      <div
        class="mb-8 md:mb-12 transition-all duration-1000 ease-out"
        style={{
          opacity: mounted() ? 1 : 0,
          transform: mounted() ? "translateY(0)" : "translateY(-20px)",
        }}
      >
        <p class="text-stone-600 text-lg">
          <Show when={totalEvents() > 0} fallback="No events scheduled">
            {totalEvents()} {totalEvents() === 1 ? "event" : "events"} today
          </Show>
        </p>
      </div>

      {/* Events list */}
      <Show when={totalEvents() > 0} fallback={<EmptyState />}>
        <div class="space-y-8">
          {/* Upcoming Events */}
          <Show when={upcomingEvents().length > 0}>
            <div
              class="transition-all duration-1000 delay-200 ease-out"
              style={{
                opacity: mounted() ? 1 : 0,
                transform: mounted() ? "translateY(0)" : "translateY(20px)",
              }}
            >
              <h2 class="text-xl font-semibold text-stone-800 mb-4 flex items-center gap-2">
                <span>Upcoming</span>
                <span class="text-sm font-normal text-stone-500">
                  ({upcomingEvents().length})
                </span>
              </h2>
              <div class="space-y-3">
                <For each={upcomingEvents()}>
                  {(event) => <EventItem event={event} />}
                </For>
              </div>
            </div>
          </Show>

          {/* Past Events */}
          <Show when={pastEvents().length > 0}>
            <div
              class="transition-all duration-1000 delay-300 ease-out"
              style={{
                opacity: mounted() ? 1 : 0,
                transform: mounted() ? "translateY(0)" : "translateY(20px)",
              }}
            >
              <h2 class="text-xl font-semibold text-stone-800 mb-4 flex items-center gap-2 opacity-60">
                <span>Earlier today</span>
                <span class="text-sm font-normal text-stone-500">
                  ({pastEvents().length})
                </span>
              </h2>
              <div class="space-y-3 opacity-60">
                <For each={pastEvents()}>
                  {(event) => <EventItem event={event} />}
                </For>
              </div>
            </div>
          </Show>
        </div>
      </Show>

    </div>
  );
};

export default TodaysEventsView;
