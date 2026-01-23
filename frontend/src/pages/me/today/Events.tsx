import { Component, createMemo, For, Show } from "solid-js";
import { useStreamingData } from "@/providers/streamingData";
import { usePageAnimation } from "@/utils/navigation";
import { EventItem } from "@/components/events/EventItem";

const EmptyState: Component = () => null;

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
        <Show when={totalEvents() > 0}>
          <p class="text-stone-600 text-lg">
            {totalEvents()} {totalEvents() === 1 ? "event" : "events"} today
          </p>
        </Show>
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
