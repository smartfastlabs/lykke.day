import { Component, For, Show, createMemo, createSignal, onMount, onCleanup } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faClock } from "@fortawesome/free-solid-svg-icons";
import type { Event, Task } from "@/types/api";
import { getTime } from "@/utils/dates";
import { getTypeIcon, getCategoryIcon } from "@/utils/icons";
import { SwipeableItem } from "@/components/shared/SwipeableItem";
import { useStreamingData } from "@/providers/streaming-data";

export interface UpcomingSectionProps {
  events: Event[];
  tasks: Task[];
}

const formatDateTime = (dateTimeStr: string): string => {
  const date = new Date(dateTimeStr);
  return date
    .toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    .toLowerCase()
    .replace(" ", "");
};

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

const EventItem: Component<{ event: Event; currentTime: () => Date }> = (props) => {
  const icon = () => getTypeIcon("EVENT");
  const categoryLabel = () => formatCategory(props.event.category);
  const isCurrentlyOccurring = createMemo(() => {
    const now = props.currentTime();
    const start = new Date(props.event.starts_at);
    const end = props.event.ends_at ? new Date(props.event.ends_at) : null;
    return start <= now && (!end || end >= now);
  });

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
          <p class="text-xs text-stone-500">
            {isCurrentlyOccurring() ? "Now" : formatDateTime(props.event.starts_at)}
          </p>
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
    getCategoryIcon(props.task.category) ||
    getTypeIcon(props.task.type);
  
  const isPastDue = createMemo(() => {
    const time = taskTime();
    if (!time) return false;
    // Note: This uses the current time at render, which is fine for display purposes
    // The main filtering happens in the parent component with the reactive now() signal
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

export const UpcomingSection: Component<UpcomingSectionProps> = (props) => {
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

  const upcomingEvents = createMemo(() => {
    const currentTime = now();
    const thirtyMinutesFromNow = new Date(currentTime.getTime() + 30 * 60 * 1000);
    
    return props.events
      .filter((event) => {
        // Exclude all-day events
        if (isAllDayEvent(event)) {
          return false;
        }
        
        const start = new Date(event.starts_at);
        const end = event.ends_at ? new Date(event.ends_at) : null;
        
        // Exclude if currently occurring (those go in Right Now section)
        if (start <= currentTime && (!end || end >= currentTime)) {
          return false;
        }
        
        // Include if starting within next 30 minutes
        return start >= currentTime && start <= thirtyMinutesFromNow;
      })
      .sort((a, b) => {
        const aTime = new Date(a.starts_at).getTime();
        const bTime = new Date(b.starts_at).getTime();
        return aTime - bTime;
      });
  });

  const upcomingTasks = createMemo(() => {
    const currentTime = now();
    const thirtyMinutesFromNow = new Date(currentTime.getTime() + 30 * 60 * 1000);
    
    return props.tasks
      .filter((task) => {
        // Skip completed or punted tasks
        if (task.status === "COMPLETE" || task.status === "PUNT") {
          return false;
        }

        const taskTime = getTaskTime(task);
        if (!taskTime) return false;

        // Exclude if past due (those go in Right Now section)
        if (taskTime < currentTime) {
          return false;
        }

        // Include if due within next 30 minutes
        return taskTime >= currentTime && taskTime <= thirtyMinutesFromNow;
      })
      .sort((a, b) => {
        const aTime = getTaskTime(a);
        const bTime = getTaskTime(b);
        if (!aTime || !bTime) return 0;
        return aTime.getTime() - bTime.getTime();
      });
  });

  const hasUpcomingItems = createMemo(() => 
    upcomingEvents().length > 0 || upcomingTasks().length > 0
  );

  return (
    <Show when={hasUpcomingItems()}>
      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
        <div class="flex items-center gap-3">
          <Icon icon={faClock} class="w-5 h-5 fill-amber-600" />
          <p class="text-xs uppercase tracking-wide text-amber-700">Upcoming</p>
        </div>
        
        <Show when={upcomingEvents().length > 0}>
          <div class="space-y-3">
            <For each={upcomingEvents()}>
              {(event) => <EventItem event={event} currentTime={now} />}
            </For>
          </div>
        </Show>
        
        <Show when={upcomingTasks().length > 0}>
          <div class="space-y-3">
            <For each={upcomingTasks()}>
              {(task) => <TaskItem task={task} />}
            </For>
          </div>
        </Show>
      </div>
    </Show>
  );
};
