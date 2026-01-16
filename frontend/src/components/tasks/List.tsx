import { Component, For, Show } from "solid-js";
import type { Accessor } from "solid-js";
import { getCategoryIcon, getTypeIcon } from "@/utils/icons";
import { TaskStatus, Task, TaskSchedule } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streaming-data";
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
      return "bg-amber-50/30 italic";
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
    >
      <div class="flex items-center gap-4">
        {/* Time column */}
        <div class="w-14 flex-shrink-0 text-right">
          <Show
            when={time()?.primary}
            fallback={<span class="text-xs text-stone-300">—</span>}
          >
            <span
              class={`text-xs tabular-nums ${
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
            <Icon icon={icon()!} />
          </Show>
        </span>

        {/* Task name */}
        <div class="flex-1 min-w-0">
          <span
            class={`text-sm truncate block ${
              props.task.status === "COMPLETE"
                ? "line-through text-stone-400"
                : "text-stone-800"
            }`}
          >
            {props.task.name.replace("Routine: ", "")}
          </span>
        </div>

        <Show when={props.task.status === "COMPLETE"}>
          <div class="flex-shrink-0 w-4 text-amber-600">
            <Icon key="checkMark" />
          </div>
        </Show>
      </div>
    </SwipeableItem>
  );
};

// Sorting helpers
const parseTimeToMinutes = (timeStr?: string | null): number | null => {
  if (!timeStr) return null;
  const [h, m] = timeStr.split(":").map(Number);
  return h * 60 + m;
};

const getTaskSortTime = (task: Task): number => {
  const schedule = task.schedule;
  if (!schedule) return Infinity;

  // Use start_time for TIME_WINDOW and FIXED_TIME
  if (schedule.start_time) {
    return parseTimeToMinutes(schedule.start_time) ?? Infinity;
  }
  // Use end_time for DEADLINE
  if (schedule.end_time) {
    return parseTimeToMinutes(schedule.end_time) ?? Infinity;
  }
  // Use available_time as fallback
  if (schedule.available_time) {
    return parseTimeToMinutes(schedule.available_time) ?? Infinity;
  }
  return Infinity;
};

const sortTasks = (tasks: Task[]): Task[] => {
  return [...tasks].sort((a, b) => getTaskSortTime(a) - getTaskSortTime(b));
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
