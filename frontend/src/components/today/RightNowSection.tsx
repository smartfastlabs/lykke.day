import { Component, For, Show, createMemo } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faCircle } from "@fortawesome/free-solid-svg-icons";
import type { Event, Task } from "@/types/api";
import { getTime } from "@/utils/dates";
import { getTypeIcon, getCategoryIcon } from "@/utils/icons";
import { SwipeableItem } from "@/components/shared/SwipeableItem";
import { useStreamingData } from "@/providers/streaming-data";

export interface RightNowSectionProps {
  events: Event[];
  tasks: Task[];
}

const formatTimeString = (timeStr: string): string => {
  const [h, m] = timeStr.split(":");
  const hour = parseInt(h);
  const ampm = hour >= 12 ? "p" : "a";
  const hour12 = hour % 12 || 12;
  return `${hour12}:${m}${ampm}`;
};

const getTaskTime = (task: Task): Date | null => {
  const taskDate = task.scheduled_date;
  if (!taskDate || !task.schedule) return null;

  const schedule = task.schedule;

  // For FIXED_TIME, use start_time
  if (schedule.timing_type === "FIXED_TIME" && schedule.start_time) {
    return getTime(taskDate, schedule.start_time);
  }

  // For DEADLINE, use end_time
  if (schedule.timing_type === "DEADLINE" && schedule.end_time) {
    return getTime(taskDate, schedule.end_time);
  }

  // For others, use available_time or start_time as fallback
  if (schedule.available_time) {
    return getTime(taskDate, schedule.available_time);
  }

  if (schedule.start_time) {
    return getTime(taskDate, schedule.start_time);
  }

  return null;
};

const formatCategory = (category?: Event["category"]): string =>
  (category ?? "OTHER").toLowerCase().replace("_", " ");

const EventItem: Component<{ event: Event }> = (props) => {
  const icon = () => getTypeIcon("EVENT");
  const categoryLabel = () => formatCategory(props.event.category);

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
          <p class="text-xs text-stone-500">Now</p>
          <span class="text-[10px] font-medium uppercase tracking-wide text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">
            {categoryLabel()}
          </span>
        </div>
      </div>
    </div>
  );
};

const getStatusClasses = (status: Task["status"]): string => {
  switch (status) {
    case "COMPLETE":
      return "bg-stone-50/50";
    case "PUNT":
      return "bg-amber-50/30 italic";
    default:
      return "";
  }
};

const TaskItem: Component<{ task: Task }> = (props) => {
  const taskTime = () => getTaskTime(props.task);
  const timeDisplay = createMemo(() => {
    const time = taskTime();
    if (!time) return null;
    const schedule = props.task.schedule;
    if (!schedule) return null;

    if (schedule.start_time) {
      return formatTimeString(schedule.start_time);
    }
    if (schedule.end_time) {
      return formatTimeString(schedule.end_time);
    }
    return null;
  });

  const icon = () =>
    getCategoryIcon(props.task.category) || getTypeIcon(props.task.type);

  const isPastDue = createMemo(() => {
    const time = taskTime();
    if (!time) return false;
    return time < new Date();
  });

  const { setTaskStatus } = useStreamingData();

  return (
    <SwipeableItem
      onSwipeRight={() => setTaskStatus(props.task, "COMPLETE")}
      onSwipeLeft={() => setTaskStatus(props.task, "PUNT")}
      rightLabel="✅ Complete Task"
      leftLabel="⏸ Punt Task"
      statusClass={getStatusClasses(props.task.status)}
      compact={true}
    >
      <div class="flex items-start gap-3">
        <div class="mt-0.5">
          <Show when={icon()}>
            <Icon icon={icon()!} class="w-4 h-4" />
          </Show>
        </div>
        <div class="flex-1">
          <p
            class="text-sm font-semibold"
            classList={{
              "text-red-600": isPastDue(),
              "text-stone-800": !isPastDue(),
            }}
          >
            {props.task.name}
          </p>
          <Show when={timeDisplay()}>
            <p
              class="text-xs"
              classList={{
                "text-red-500": isPastDue(),
                "text-stone-500": !isPastDue(),
              }}
            >
              {timeDisplay()}
              {isPastDue() && " (past due)"}
            </p>
          </Show>
        </div>
      </div>
    </SwipeableItem>
  );
};

const isAllDayEvent = (event: Event): boolean => {
  const start = new Date(event.starts_at);
  const end = event.ends_at ? new Date(event.ends_at) : null;
  if (!end) return false;
  const diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
  return diffHours >= 23;
};

export const RightNowSection: Component<RightNowSectionProps> = (props) => {
  const now = new Date();

  const ongoingEvents = createMemo(() => {
    return props.events
      .filter((event) => {
        // Exclude all-day events
        if (isAllDayEvent(event)) {
          return false;
        }

        const start = new Date(event.starts_at);
        const end = event.ends_at ? new Date(event.ends_at) : null;

        // Only include if currently occurring
        return start <= now && (!end || end >= now);
      })
      .sort((a, b) => {
        const aTime = new Date(a.starts_at).getTime();
        const bTime = new Date(b.starts_at).getTime();
        return aTime - bTime;
      });
  });

  const pastDueTasks = createMemo(() => {
    return props.tasks
      .filter((task) => {
        // Skip completed or punted tasks
        if (task.status === "COMPLETE" || task.status === "PUNT") {
          return false;
        }

        const taskTime = getTaskTime(task);
        if (!taskTime) return false;

        // Only include if past due (past start time or end time)
        return taskTime < now;
      })
      .sort((a, b) => {
        const aTime = getTaskTime(a);
        const bTime = getTaskTime(b);
        if (!aTime || !bTime) return 0;
        return aTime.getTime() - bTime.getTime();
      });
  });

  const hasRightNowItems = createMemo(
    () => ongoingEvents().length > 0 || pastDueTasks().length > 0
  );

  return (
    <Show when={hasRightNowItems()}>
      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
        <div class="flex items-center gap-3">
          <Icon icon={faCircle} class="w-5 h-5 fill-amber-600" />
          <p class="text-xs uppercase tracking-wide text-amber-700">
            Right Now
          </p>
        </div>

        <Show when={ongoingEvents().length > 0}>
          <div class="space-y-3">
            <For each={ongoingEvents()}>
              {(event) => <EventItem event={event} />}
            </For>
          </div>
        </Show>

        <Show when={pastDueTasks().length > 0}>
          <div class="space-y-3">
            <For each={pastDueTasks()}>
              {(task) => <TaskItem task={task} />}
            </For>
          </div>
        </Show>
      </div>
    </Show>
  );
};
