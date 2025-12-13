import { For, onMount, createSignal, createEffect, Show } from "solid-js";
import { getTime } from "../../utils/dates";
import { TaskCard } from "./card";
import { useSheppardManager } from "../../providers/sheppard";

type Task = {
  id: string;
  title: string;
  time: Date; // Each task has a Date object
  // ...other fields
};

interface TaskListProps {
  startTime: string; // e.g. "08:30"
  endTime: string; // e.g. "20:00"
  tasks: Task[];
}

export function TaskList(props: TaskListProps) {
  const HOUR_HEIGHT = 100; // px per hour
  const MINUTE_HEIGHT = HOUR_HEIGHT / 60; // pixel scale per minute
  const [now, setNow] = createSignal(new Date());
  const { setTaskStatus } = useSheppardManager();
  let scrollRef: HTMLDivElement | undefined;

  // Helper: convert "HH:mm" -> Date (for today)
  const timeStringToDate = (timeStr: string): Date => {
    const [hours, minutes] = timeStr.split(":").map(Number);
    const d = new Date();
    d.setHours(hours, minutes, 0, 0);
    return d;
  };

  const startDate = () => timeStringToDate(props.startTime);
  const endDate = () => timeStringToDate(props.endTime);

  // Generate list of hour marks
  const hours = () => {
    const list: Date[] = [];
    const current = new Date(startDate());
    while (current <= endDate()) {
      list.push(new Date(current));
      current.setHours(current.getHours() + 1, 0, 0, 0);
    }
    return list;
  };
  const completeTask = async (task: Task) => {
    return setTaskStatus(task, "COMPLETE");
  };

  const puntTask = async (task: Task) => {
    return setTaskStatus(task, "PUNTED");
  };

  // Compute offset from start time
  const offsetForTask = (task) => {
    if (task.schedule.start_time || task.schedule.end_time) {
      const time = getTime(
        task.date,
        task.schedule.start_time || task.schedule.end_time
      );
      return offsetForTime(time);
    }

    return offsetForTime(endDate());
  };

  const offsetForTime = (time: Date) => {
    const diffMs = time.getTime() - startDate().getTime();
    const diffMins = diffMs / (1000 * 60);
    return diffMins * MINUTE_HEIGHT;
  };

  // Update current time every minute
  onMount(() => {
    const interval = setInterval(() => setNow(new Date()), 60_000);
    // Scroll to current time once
    const offset = offsetForTime(new Date());
    scrollRef?.scrollTo({ top: offset - 30, behavior: "smooth" });
    console.log("Scrolling to offset", offset);
    return () => clearInterval(interval);
  });

  // Recompute offset dynamically if time changes
  createEffect(() => {
    offsetForTime(now());
  });

  return (
    <div
      ref={scrollRef}
      class="overflow-y-scroll relative w-full h-screen  bg-gray-50 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      style="touch-action: pan-y"
    >
      {/* Hour Marks */}
      <For each={hours()}>
        {(hour) => (
          <div
            className="absolute left-0 w-full flex"
            style={{
              top: `${offsetForTime(hour)}px`,
              height: `${HOUR_HEIGHT}px`,
            }}
          >
            {/* Left column (~15%) */}
            <div className="w-[15%] relative">
              <span className="absolute left-3 -top-2 text-xs text-gray-400">
                {hour.getHours().toString().padStart(2, "0")}:00
              </span>
            </div>

            {/* Right column (~85%) */}
            <div className="w-[85%] relative">
              <div className="absolute w-full border-t border-gray-400"></div>
            </div>
          </div>
        )}
      </For>

      {/* Current Time Indicator */}
      <Show when={now() >= startDate() && now() <= endDate()}>
        <div
          class="absolute left-[40px] right-0 h-[2px] bg-gray-200 animate-pulse"
          style={{
            top: `${offsetForTime(now())}px`,
          }}
        >
          <div class="absolute -left-2 top-[-8px] w-5 h-5 rounded-full bg-gray-400 animate-pulse" />
        </div>
      </Show>

      {/* Tasks */}
      <For each={props.tasks()}>
        {(task) => (
          <div
            class="absolute inset-x-0"
            style={{
              top: `${offsetForTask(task)}px`,
              left: "60px",
              right: "0px",
            }}
          >
            <TaskCard
              task={task}
              onSwipeRight={completeTask}
              onSwipeLeft={puntTask}
            />
          </div>
        )}
      </For>

      {/* Spacer at bottom */}
      <div
        class="absolute inset-x-0 min-h-screen"
        style={{
          top: `${offsetForTime(endDate()) + 200}px`,
        }}
      />
    </div>
  );
}

export default TaskList;
