import { Component, For, Show } from "solid-js";
import type { Accessor } from "solid-js";
import { getCategoryIcon, getTypeIcon } from "@/utils/icons";
import { TaskStatus, Task, TaskSchedule } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import { faXmark } from "@fortawesome/free-solid-svg-icons";
import { useStreamingData } from "@/providers/streamingData";
import { SwipeableItem } from "@/components/shared/SwipeableItem";

export const formatTimeString = (timeStr: string): string => {
  const [h, m] = timeStr.split(":");
  const hour = parseInt(h);
  const ampm = hour >= 12 ? "p" : "a";
  const hour12 = hour % 12 || 12;
  return `${hour12}:${m}${ampm}`;
};

interface TimeDisplay {
  primary: string | null;
  secondary: string | null;
}

const getTimeDisplay = (schedule?: TaskSchedule): TimeDisplay | null => {
  if (!schedule) return null;

  if (schedule.timing_type === "TIME_WINDOW" && schedule.start_time) {
    return {
      primary: formatTimeString(schedule.start_time),
      secondary: schedule.end_time ? formatTimeString(schedule.end_time) : null,
    };
  }

  if (schedule.timing_type === "FIXED_TIME" && schedule.start_time) {
    return {
      primary: formatTimeString(schedule.start_time),
      secondary: null,
    };
  }

  if (schedule.timing_type === "DEADLINE") {
    return {
      primary: schedule.end_time
        ? `by ${formatTimeString(schedule.end_time)}`
        : null,
      secondary: null,
    };
  }
  if (schedule.timing_type === "FLEXIBLE") {
    if (schedule.available_time) {
      return {
        primary: `after ${formatTimeString(schedule.available_time)}`,
        secondary: null,
      };
    }
    if (schedule.end_time) {
      return {
        primary: `before ${formatTimeString(schedule.end_time)}`,
        secondary: null,
      };
    }
  }

  return null;
};

const getStatusClasses = (status: TaskStatus): string => {
  switch (status) {
    case "COMPLETE":
      return "bg-stone-50/50";
    case "PUNT":
      return "bg-amber-50/30";
    case "NOT_READY":
      return "opacity-40";
    default:
      return "";
  }
};

const TaskItem: Component<{ task: Task }> = (props) => {
  const time = () => getTimeDisplay(props.task.schedule ?? undefined);
  const icon = () =>
    getCategoryIcon(props.task.category) || getTypeIcon(props.task.type);

  const { setTaskStatus } = useStreamingData();

  return (
    <SwipeableItem
      onSwipeRight={() => setTaskStatus(props.task, "COMPLETE")}
      onSwipeLeft={() => setTaskStatus(props.task, "PUNT")}
      rightLabel="✅ Complete Task"
      leftLabel="🗑 Punt Task"
      statusClass={getStatusClasses(props.task.status)}
      compact={true}
    >
      <div class="flex items-center gap-2">
        {/* Time column */}
        <div class="w-16 flex-shrink-0 text-right">
          <Show
            when={time()?.primary}
            fallback={<span class="text-[10px] text-stone-300">—</span>}
          >
            <span
              class={`text-[10px] tabular-nums whitespace-nowrap ${
                time()?.primary === "flexible"
                  ? "text-stone-400 italic"
                  : "text-stone-500"
              }`}
            >
              {time()?.primary}
            </span>
          </Show>
        </div>

        {/* Category/Type icon */}
        <span class="w-4 flex-shrink-0 flex items-center justify-center text-amber-600">
          <Show when={icon()}>
            <Icon icon={icon()!} class="w-3 h-3" />
          </Show>
        </span>

        {/* Task name */}
        <div class="flex-1 min-w-0">
          <span
            class="text-xs truncate block"
            classList={{
              "line-through text-stone-400": props.task.status === "COMPLETE",
              "text-stone-800": props.task.status !== "COMPLETE",
              "text-orange-700 italic": props.task.status === "PUNT",
            }}
          >
            {props.task.name.replace("Routine: ", "")}
          </span>
        </div>

        <Show when={props.task.status === "COMPLETE"}>
          <div class="flex-shrink-0 w-4 text-amber-600">
            <Icon key="checkMark" class="w-3 h-3" />
          </div>
        </Show>
        <Show when={props.task.status === "PUNT"}>
          <div class="flex-shrink-0 w-4 text-red-500">
            <Icon icon={faXmark} class="w-3 h-3" />
          </div>
        </Show>
      </div>
    </SwipeableItem>
  );
};

// Sorting helpers
const getSortableTime = (schedule: TaskSchedule): string | null => {
  switch (schedule.timing_type) {
    case "TIME_WINDOW":
    case "FIXED_TIME":
      return schedule.start_time ?? null;
    case "DEADLINE":
      return schedule.end_time ?? null;
    case "FLEXIBLE":
      return schedule.available_time ?? schedule.end_time ?? null;
    default:
      return (
        schedule.start_time ??
        schedule.end_time ??
        schedule.available_time ??
        null
      );
  }
};

const parseDateTimeToTimestamp = (dateStr: string, timeStr: string): number => {
  const [yearStr, monthStr, dayStr] = dateStr.split("-");
  const [hourStr, minuteStr] = timeStr.split(":");
  const year = Number(yearStr);
  const month = Number(monthStr);
  const day = Number(dayStr);
  const hour = Number(hourStr);
  const minute = Number(minuteStr);

  const date = new Date(year, month - 1, day, hour, minute);
  const timestamp = date.getTime();
  return Number.isNaN(timestamp) ? Number.POSITIVE_INFINITY : timestamp;
};

const getTaskSortTimestamp = (task: Task): number => {
  const schedule = task.schedule;
  if (!schedule) return Number.POSITIVE_INFINITY;

  const timeStr = getSortableTime(schedule);
  if (!timeStr) return Number.POSITIVE_INFINITY;

  return parseDateTimeToTimestamp(task.scheduled_date, timeStr);
};

const sortTasks = (tasks: Task[]): Task[] => {
  return [...tasks].sort(
    (a, b) => getTaskSortTimestamp(a) - getTaskSortTimestamp(b)
  );
};

interface TaskListProps {
  tasks: Accessor<Task[]>;
}

const TaskList: Component<TaskListProps> = (props) => {
  const tasks = () => sortTasks(props.tasks() ?? []);

  return (
    <>
      <For each={tasks()}>{(task) => <TaskItem task={task} />}</For>
    </>
  );
};

export default TaskList;
