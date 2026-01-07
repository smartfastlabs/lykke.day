import { createSignal, Component, For, Show } from "solid-js";
import type { Accessor } from "solid-js";
import { getCategoryIcon, getTypeIcon } from "@/utils/icons";
import { TaskStatus, Task, TaskSchedule } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import { useSheppard } from "@/providers/sheppard";

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
      return "bg-gray-100";
    case "PUNT":
      return "bg-gray-50 italic";
    case "NOT_READY":
      return "opacity-40";
    default:
      return "";
  }
};

const TaskItem: Component<{ task: Task }> = (props) => {
  const time = () => getTimeDisplay(props.task.schedule ?? undefined);
  const icon = () =>
    getCategoryIcon(props.task.category) ||
    getTypeIcon(props.task.task_definition?.type);

  const { setTaskStatus } = useSheppard();

  const [translateX, setTranslateX] = createSignal(0);
  let startX = 0;
  let startY = 0;
  let isSwiping = false;

  const handleTouchStart = (e: TouchEvent) => {
    const touch = e.touches[0];
    startX = touch.clientX;
    startY = touch.clientY;
    isSwiping = false;
  };

  const handleTouchMove = (e: TouchEvent) => {
    const touch = e.touches[0];
    const dx = touch.clientX - startX;
    const dy = touch.clientY - startY;

    // Detect if user is swiping horizontally or vertically
    if (!isSwiping) {
      if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 10) {
        isSwiping = true;
      } else if (Math.abs(dy) > 10) {
        // user is scrolling vertically — bail out
        return;
      }
    }

    if (isSwiping) {
      e.preventDefault(); // only prevent default when actually swiping horizontally
      setTranslateX(dx);
    }
  };

  const handleTouchEnd = () => {
    console.log("touch end");
    if (isSwiping) {
      const x = translateX();
      const threshold = 100;
      if (x > threshold) {
        setTaskStatus(props.task, "COMPLETE");
      } else if (x < -threshold) {
        setTaskStatus(props.task, "PUNT");
      }
      setTranslateX(0);
    }
    isSwiping = false;
  };

  return (
    <div
      class="relative w-full overflow-hidden select-none"
      style="touch-action: pan-y"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <div class="absolute inset-0 bg-gray-100 flex justify-between items-center px-6 text-sm font-medium pointer-events-none">
        <span class="text-green-600">✅ Complete Task</span>
        <span class="text-red-600">🗑 Punt Task</span>
      </div>

      {/* Foreground Card */}
      <div
        class="relative bg-white p-3 transition-transform duration-150 active:scale-[0.97]"
        style={{
          transform: `translateX(${translateX()}px)`,
          transition: translateX() === 0 ? "transform 0.2s ease-out" : "none",
        }}
        role="button"
      >
        <div
          class={`group px-5 py-3.5 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer ${getStatusClasses(
            props.task.status
          )}`}
        >
          <div class="flex items-center gap-4">
            {/* Time column */}
            <div class="w-14 flex-shrink-0 text-right">
              <Show
                when={time()?.primary}
                fallback={<span class="text-xs text-gray-300">—</span>}
              >
                <span
                  class={`text-xs tabular-nums ${
                    time()?.primary === "flexible"
                      ? "text-gray-400 italic"
                      : "text-gray-500"
                  }`}
                >
                  {time()?.primary}
                </span>
              </Show>
            </div>

            {/* Category/Type icon */}
            <span class="w-4 flex-shrink-0 flex items-center justify-center">
              <Show when={icon()}>
                <Icon icon={icon()!} />
              </Show>
            </span>

            {/* Task name */}
            <div class="flex-1 min-w-0">
              <span
                class={`text-sm truncate block ${
                  props.task.status === "COMPLETE"
                    ? "line-through text-gray-400"
                    : "text-gray-800"
                }`}
              >
                {props.task.name.replace("Routine: ", "")}
              </span>
            </div>

            <Show when={props.task.status === "COMPLETE"}>
              <div class="flex-shrink-0 w-4">
                <Icon key="checkMark" />
              </div>
            </Show>
          </div>
        </div>
      </div>
    </div>
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
