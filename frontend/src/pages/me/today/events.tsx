import {
  Component,
  createMemo,
  For,
  Show,
  createSignal,
  onMount,
} from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import type { Event } from "@/types/api";
import { Icon } from "solid-heroicons";
import { calendar, clock, users } from "solid-heroicons/outline";

const formatTime = (dateTimeStr: string): string => {
  const date = new Date(dateTimeStr);
  return date
    .toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    .toLowerCase()
    .replace(" ", "");
};

const formatDuration = (startStr: string, endStr?: string | null): string => {
  if (!endStr) return "";

  const start = new Date(startStr);
  const end = new Date(endStr);
  const durationMs = end.getTime() - start.getTime();
  const minutes = Math.floor(durationMs / 60000);

  if (minutes < 60) return `${minutes}m`;

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
};

const getCategoryColor = (category?: Event["category"]): string => {
  switch (category) {
    case "WORK":
      return "from-blue-500/80 to-indigo-600/80";
    case "PERSONAL":
      return "from-amber-500/80 to-orange-600/80";
    case "FAMILY":
      return "from-emerald-500/80 to-green-600/80";
    case "SOCIAL":
      return "from-purple-500/80 to-pink-600/80";
    default:
      return "from-stone-500/80 to-stone-600/80";
  }
};

const getCategoryLabel = (category?: Event["category"]): string => {
  return (category ?? "OTHER").toLowerCase().replace("_", " ");
};

const EventCard: Component<{ event: Event; index: number }> = (props) => {
  const duration = () =>
    formatDuration(props.event.starts_at, props.event.ends_at);
  const hasAttendees = () => (props.event.people?.length ?? 0) > 0;

  return (
    <div
      class="group bg-white/60 backdrop-blur-sm border border-white/70 rounded-2xl p-6 hover:bg-white/80 hover:shadow-xl hover:shadow-amber-900/10 transition-all duration-300"
      style={{
        animation: `fadeInUp 0.6s ease-out ${props.index * 0.1}s both`,
      }}
    >
      <div class="flex items-start gap-4">
        <div
          class={`flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br ${getCategoryColor(props.event.category)} flex items-center justify-center group-hover:scale-105 transition-transform duration-300`}
        >
          <Icon path={calendar} class="w-6 h-6 text-white" />
        </div>

        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between gap-3 mb-2">
            <h3 class="text-stone-900 font-semibold text-lg leading-snug">
              {props.event.name}
            </h3>
            <span class="flex-shrink-0 text-[10px] font-medium uppercase tracking-wide text-stone-600 bg-stone-100 rounded-full px-2.5 py-1">
              {getCategoryLabel(props.event.category)}
            </span>
          </div>

          <div class="flex flex-wrap items-center gap-3 text-sm text-stone-600">
            <div class="flex items-center gap-1.5">
              <Icon path={clock} class="w-4 h-4" />
              <span>{formatTime(props.event.starts_at)}</span>
              <Show when={duration()}>
                <span class="text-stone-400">•</span>
                <span class="text-stone-500">{duration()}</span>
              </Show>
            </div>

            <Show when={hasAttendees()}>
              <div class="flex items-center gap-1.5">
                <Icon path={users} class="w-4 h-4" />
                <span>
                  {props.event.people!.length}{" "}
                  {props.event.people!.length === 1 ? "person" : "people"}
                </span>
              </div>
            </Show>
          </div>
        </div>
      </div>
    </div>
  );
};

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
  const { events } = useSheppard();
  const [mounted, setMounted] = createSignal(false);

  onMount(() => {
    setTimeout(() => setMounted(true), 50);
  });

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
                  {(event, index) => <EventCard event={event} index={index()} />}
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
                  {(event, index) => <EventCard event={event} index={index()} />}
                </For>
              </div>
            </div>
          </Show>
        </div>
      </Show>

      {/* Animation styles */}
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default TodaysEventsView;
