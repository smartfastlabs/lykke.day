import { Component, For, Show, createMemo } from "solid-js";
import type { Accessor } from "solid-js";
import type { Task, TimeWindow } from "@/types/api";
import { getCategoryIcon, getTypeIcon } from "@/utils/icons";
import { Icon } from "@/components/shared/Icon";

const formatTimeString = (timeStr: string): string => {
  const [h, m] = timeStr.split(":");
  const hour = Number.parseInt(h ?? "", 10);
  if (Number.isNaN(hour)) return timeStr;
  const ampm = hour >= 12 ? "p" : "a";
  const hour12 = hour % 12 || 12;
  return `${hour12}:${m}${ampm}`;
};

const getTimeLabel = (timeWindow?: TimeWindow | null): string | null => {
  if (!timeWindow) return null;
  if (timeWindow.start_time && timeWindow.end_time) {
    return `${formatTimeString(timeWindow.start_time)}–${formatTimeString(
      timeWindow.end_time,
    )}`;
  }
  if (timeWindow.start_time) return formatTimeString(timeWindow.start_time);
  if (timeWindow.end_time) return `by ${formatTimeString(timeWindow.end_time)}`;
  if (timeWindow.available_time)
    return `after ${formatTimeString(timeWindow.available_time)}`;
  return null;
};

export interface ReadOnlyTaskListProps {
  tasks: Accessor<Task[]>;
  onItemClick?: (task: Task) => void;
}

export const ReadOnlyTaskList: Component<ReadOnlyTaskListProps> = (props) => {
  const items = createMemo(() => props.tasks() ?? []);

  return (
    <div class="space-y-2">
      <For each={items()}>
        {(task) => {
          const time = () => getTimeLabel(task.time_window ?? undefined);
          const icon = () =>
            getCategoryIcon(task.category) || getTypeIcon(task.type);

          const handleClick = () => props.onItemClick?.(task);
          return (
            <div
              class={`bg-white/70 border border-white/70 shadow shadow-amber-900/5 rounded-2xl px-4 py-3 backdrop-blur-sm ${
                props.onItemClick ? "cursor-pointer hover:bg-white/90" : ""
              }`}
              onClick={handleClick}
            >
              <div class="flex items-center gap-3">
                <div class="w-14 flex-shrink-0 text-right">
                  <Show
                    when={time()}
                    fallback={<span class="text-xs text-stone-400"> </span>}
                  >
                    <span class="text-xs tabular-nums text-stone-500 whitespace-nowrap">
                      {time()}
                    </span>
                  </Show>
                </div>
                <span class="w-4 flex-shrink-0 flex items-center justify-center">
                  <Show when={icon()}>
                    <Icon icon={icon()!} />
                  </Show>
                </span>
                <div class="flex-1 min-w-0">
                  <span class="text-sm text-stone-800 truncate block">
                    {task.name}
                  </span>
                </div>
              </div>
            </div>
          );
        }}
      </For>
    </div>
  );
};

export default ReadOnlyTaskList;
