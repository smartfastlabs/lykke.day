import { Component, For, Show, createSignal } from "solid-js";
import type { Accessor } from "solid-js";
import { getCategoryIcon, getTypeIcon } from "@/utils/icons";
import { TaskStatus, Task, TimeWindow } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streamingData";
import { SwipeableItem } from "@/components/shared/SwipeableItem";
import SnoozeActionModal from "@/components/shared/SnoozeActionModal";

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

const getTimeDisplay = (timeWindow?: TimeWindow): TimeDisplay | null => {
  if (!timeWindow) return null;

  // Time window: both start and end
  if (timeWindow.start_time && timeWindow.end_time) {
    return {
      primary: formatTimeString(timeWindow.start_time),
      secondary: formatTimeString(timeWindow.end_time),
    };
  }

  // Fixed time: start_time only
  if (timeWindow.start_time) {
    return {
      primary: formatTimeString(timeWindow.start_time),
      secondary: null,
    };
  }

  // Deadline: end_time only
  if (timeWindow.end_time) {
    return {
      primary: `by ${formatTimeString(timeWindow.end_time)}`,
      secondary: null,
    };
  }

  // Flexible: available_time only
  if (timeWindow.available_time) {
    return {
      primary: `after ${formatTimeString(timeWindow.available_time)}`,
      secondary: null,
    };
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
    case "SNOOZE":
      return "bg-sky-50/50";
    default:
      return "";
  }
};

const getStatusPill = (
  status: TaskStatus
): { label: string; className: string } | null => {
  switch (status) {
    case "COMPLETE":
      return {
        label: "Done",
        className: "bg-emerald-100 text-emerald-700",
      };
    case "PUNT":
      return {
        label: "Punted",
        className: "bg-amber-100 text-amber-700",
      };
    case "SNOOZE":
      return {
        label: "Snoozed",
        className: "bg-sky-100 text-sky-700",
      };
    default:
      return null;
  }
};

const TaskRowContent: Component<{ task: Task }> = (props) => {
  const time = () => getTimeDisplay(props.task.time_window ?? undefined);
  const icon = () =>
    getCategoryIcon(props.task.category) || getTypeIcon(props.task.type);
  const statusPill = () => getStatusPill(props.task.status);

  return (
    <div class="flex items-center justify-start gap-2">
      {/* Category/Type icon */}
      <span class="flex-shrink-0 flex items-center justify-center text-amber-600">
        <Show when={icon()}>
          <Icon icon={icon()!} class="w-3 h-3" />
        </Show>
      </span>

      {/* Task name */}
      <div class="flex-1 min-w-0 text-left">
        <span
          class="text-xs truncate block text-left"
          classList={{
            "line-through text-stone-400": props.task.status === "COMPLETE",
            "text-orange-700 italic": props.task.status === "PUNT",
            "text-sky-700 italic": props.task.status === "SNOOZE",
            "text-stone-800":
              props.task.status !== "COMPLETE" &&
              props.task.status !== "PUNT" &&
              props.task.status !== "SNOOZE",
          }}
        >
          {props.task.name
            .replace("ROUTINE DEFINITION: ", "")
            .replace("Routine Definition: ", "")}
        </span>
      </div>

      {/* Time - right justified, only when present */}
      <Show
        when={
          time()?.primary &&
          props.task.status !== "COMPLETE" &&
          props.task.status !== "PUNT"
        }
      >
        <div class="flex-shrink-0 ml-auto text-right">
          <span
            class={`text-[10px] tabular-nums whitespace-nowrap ${
              time()?.primary === "flexible"
                ? "text-stone-400 italic"
                : "text-stone-500"
            }`}
          >
            {time()?.primary}
          </span>
        </div>
      </Show>

      <Show when={statusPill()}>
        <span
          class={`flex-shrink-0 ml-2 px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wide ${statusPill()!.className}`}
        >
          {statusPill()!.label}
        </span>
      </Show>
    </div>
  );
};

const StaticTaskItem: Component<{ task: Task }> = (props) => {
  return (
    <div class="relative w-full overflow-hidden select-none">
      {/* Foreground Card (non-swipeable) */}
      <div class="relative">
        <div class="group bg-white rounded-xl hover:shadow-lg hover:shadow-amber-900/5 transition-all duration-300">
          <div class={`px-5 py-1 ${getStatusClasses(props.task.status)}`}>
            <TaskRowContent task={props.task} />
          </div>
        </div>
      </div>
    </div>
  );
};

const SwipeableTaskItem: Component<{ task: Task }> = (props) => {
  const { setTaskStatus, snoozeTask } = useStreamingData();
  const [pendingTask, setPendingTask] = createSignal<Task | null>(null);

  const handleClose = () => setPendingTask(null);
  const handlePunt = async () => {
    const task = pendingTask();
    if (!task) return;
    handleClose();
    await setTaskStatus(task, "PUNT");
  };
  const handleSnooze = async (minutes: number) => {
    const task = pendingTask();
    if (!task) return;
    handleClose();
    const snoozedUntil = new Date(
      Date.now() + minutes * 60 * 1000
    ).toISOString();
    await snoozeTask(task, snoozedUntil);
  };

  return (
    <>
      <SwipeableItem
        onSwipeRight={() => setTaskStatus(props.task, "COMPLETE")}
        onSwipeLeft={() => setPendingTask(props.task)}
        rightLabel="✅ Complete Task"
        leftLabel="⏸ Punt or Snooze"
        statusClass={getStatusClasses(props.task.status)}
        compact={true}
      >
        <TaskRowContent task={props.task} />
      </SwipeableItem>
      <SnoozeActionModal
        isOpen={Boolean(pendingTask())}
        title="Punt or Snooze"
        onClose={handleClose}
        onPunt={() => void handlePunt()}
        onSnooze={(minutes) => void handleSnooze(minutes)}
      />
    </>
  );
};

// Sorting helpers
const getSortableTime = (timeWindow: TimeWindow): string | null => {
  // Prefer start_time, then end_time, then available_time
  return (
    timeWindow.start_time ??
    timeWindow.end_time ??
    timeWindow.available_time ??
    null
  );
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
  const timeWindow = task.time_window;
  if (!timeWindow) return Number.POSITIVE_INFINITY;

  const timeStr = getSortableTime(timeWindow);
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
  interactive?: boolean;
}

const TaskList: Component<TaskListProps> = (props) => {
  const tasks = () => sortTasks(props.tasks() ?? []);
  const interactive = () => props.interactive ?? true;

  return (
    <>
      <For each={tasks()}>
        {(task) => (
          <>
            {interactive() ? (
              <SwipeableTaskItem task={task} />
            ) : (
              <StaticTaskItem task={task} />
            )}
          </>
        )}
      </For>
    </>
  );
};

export default TaskList;
