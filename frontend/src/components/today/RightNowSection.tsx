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
import { getTaskUpcomingTime, isTaskSnoozed } from "@/utils/tasks";
import TaskList from "@/components/tasks/List";
import { EventItem } from "@/components/events/EventItem";

export interface RightNowSectionProps {
  events: Event[];
  tasks: Task[];
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
    const currentTime = now();
    return props.tasks
      .filter((task) => {
        // Skip completed or punted tasks
        if (task.status === "COMPLETE" || task.status === "PUNT") {
          return false;
        }
        if (isTaskSnoozed(task, currentTime)) {
          return false;
        }

        const taskTime = getTaskUpcomingTime(task, currentTime);
        if (!taskTime) return false;

        // Only include if past due (past start time or end time)
        return taskTime < currentTime;
      })
      .sort((a, b) => {
        const aTime = getTaskUpcomingTime(a, currentTime);
        const bTime = getTaskUpcomingTime(b, currentTime);
        if (!aTime || !bTime) return 0;
        return aTime.getTime() - bTime.getTime();
      });
  });

  const hasRightNowItems = createMemo(
    () => ongoingEvents().length > 0 || pastDueTasks().length > 0,
  );
  return (
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
  );
};
