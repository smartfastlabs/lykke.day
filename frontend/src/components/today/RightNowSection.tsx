import {
  Component,
  For,
  Show,
  createMemo,
  createSignal,
  onMount,
  onCleanup,
} from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faCircle } from "@fortawesome/free-solid-svg-icons";
import type { Event, Task } from "@/types/api";
import TaskList from "@/components/tasks/List";
import { EventItem } from "@/components/events/EventItem";
import { FuzzyCard, FuzzyLine } from "./FuzzyCard";

export interface RightNowSectionProps {
  events: Event[];
  tasks: Task[];
  isLoading?: boolean;
}

const isAllDayEvent = (event: Event): boolean => {
  const start = new Date(event.starts_at);
  const end = event.ends_at ? new Date(event.ends_at) : null;
  if (!end) return false;
  const diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
  return diffHours >= 23;
};

export const RightNowSection: Component<RightNowSectionProps> = (props) => {
  const [now, setNow] = createSignal(new Date());

  // Update time every 30 seconds to keep the section reactive
  onMount(() => {
    const interval = setInterval(() => {
      setNow(new Date());
    }, 30000); // Update every 30 seconds

    onCleanup(() => {
      clearInterval(interval);
    });
  });

  const ongoingEvents = createMemo(() => {
    const currentTime = now();
    return props.events
      .filter((event) => {
        // Exclude all-day events
        if (isAllDayEvent(event)) {
          return false;
        }

        const start = new Date(event.starts_at);
        const end = event.ends_at ? new Date(event.ends_at) : null;

        // Only include if currently occurring
        return start <= currentTime && (!end || end >= currentTime);
      })
      .sort((a, b) => {
        const aTime = new Date(a.starts_at).getTime();
        const bTime = new Date(b.starts_at).getTime();
        return aTime - bTime;
      });
  });

  const pastDueTasks = createMemo(() => {
    return props.tasks.filter(
      (task) =>
        task.timing_status === "past-due" &&
        task.status !== "COMPLETE" &&
        task.status !== "PUNT",
    );
  });

  const hasRightNowItems = createMemo(
    () => ongoingEvents().length > 0 || pastDueTasks().length > 0,
  );
  return (
    <Show
      when={!props.isLoading}
      fallback={
        <FuzzyCard class="p-3 space-y-3">
          <div class="flex items-center gap-2">
            <div class="h-3 w-3 rounded-full bg-amber-200/90" />
            <FuzzyLine class="h-2 w-20" />
          </div>
          <div class="space-y-2">
            <FuzzyLine class="h-2 w-12" />
            <div class="space-y-2">
              <FuzzyLine class="h-3 w-full" />
              <FuzzyLine class="h-3 w-5/6" />
            </div>
          </div>
          <div class="space-y-2">
            <FuzzyLine class="h-2 w-10" />
            <div class="space-y-2">
              <FuzzyLine class="h-3 w-4/5" />
              <FuzzyLine class="h-3 w-2/3" />
            </div>
          </div>
        </FuzzyCard>
      }
    >
      <Show when={hasRightNowItems()}>
        <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-3 backdrop-blur-sm space-y-2">
          <div class="flex items-center gap-2">
            <Icon icon={faCircle} class="w-3 h-3 fill-amber-600" />
            <p class="text-[10px] uppercase tracking-wide text-amber-700">
              Right now
            </p>
          </div>

          <Show when={ongoingEvents().length > 0}>
            <div class="space-y-1">
              <p class="text-[11px] font-medium text-stone-500">Events</p>
              <For each={ongoingEvents()}>
                {(event) => <EventItem event={event} />}
              </For>
            </div>
          </Show>

          <Show when={pastDueTasks().length > 0}>
            <div class="space-y-1">
              <p class="text-[11px] font-medium text-stone-500">Tasks</p>
              <div class="space-y-1">
                <TaskList tasks={() => pastDueTasks()} />
              </div>
            </div>
          </Show>
        </div>
      </Show>
    </Show>
  );
};
