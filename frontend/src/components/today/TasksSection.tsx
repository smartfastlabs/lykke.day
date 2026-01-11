import { Component, For, Show, createMemo } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faListCheck } from "@fortawesome/free-solid-svg-icons";
import type { Task } from "@/types/api";
import { getCategoryIcon, getTypeIcon } from "@/utils/icons";

export interface TasksSectionProps {
  tasks: Task[];
  href: string;
}

const formatTimeString = (timeStr: string): string => {
  const [h, m] = timeStr.split(":");
  const hour = parseInt(h);
  const ampm = hour >= 12 ? "p" : "a";
  const hour12 = hour % 12 || 12;
  return `${hour12}:${m}${ampm}`;
};

const getTimeDisplay = (schedule?: { start_time?: string | null } | null): string | null => {
  if (!schedule?.start_time) return null;
  try {
    // start_time is in "HH:MM" format
    return formatTimeString(schedule.start_time);
  } catch {
    return null;
  }
};

const TaskItem: Component<{ task: Task }> = (props) => {
  const time = () => getTimeDisplay(props.task.schedule ?? undefined);
  const icon = () =>
    getCategoryIcon(props.task.category) ||
    getTypeIcon(props.task.type);

  return (
    <div class="flex items-start gap-3">
      <div class="mt-0.5">
        <Show when={icon()}>
          <Icon icon={icon()!} class="w-4 h-4" />
        </Show>
      </div>
      <div class="flex-1">
        <p class="text-sm font-semibold text-stone-800">{props.task.name}</p>
        <Show when={time()}>
          <p class="text-xs text-stone-500">{time()}</p>
        </Show>
      </div>
    </div>
  );
};

export const TasksSection: Component<TasksSectionProps> = (props) => {
  const importantTasks = createMemo(() =>
    props.tasks.filter(
      (t) => t.status !== "COMPLETE" && t.tags?.includes("IMPORTANT")
    )
  );

  const otherCount = createMemo(() =>
    props.tasks.filter(
      (t) => t.status !== "COMPLETE" && !t.tags?.includes("IMPORTANT")
    ).length
  );

  return (
    <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <Icon icon={faListCheck} class="w-5 h-5 fill-amber-600" />
          <p class="text-xs uppercase tracking-wide text-amber-700">Tasks</p>
        </div>
        <a
          class="text-xs font-semibold text-amber-700 hover:text-amber-800"
          href={props.href}
        >
          See all tasks
        </a>
      </div>
      <Show when={importantTasks().length > 0}>
        <For each={importantTasks()}>
          {(task) => <TaskItem task={task} />}
        </For>
      </Show>
      <Show when={otherCount() > 0}>
        <p class="text-xs text-stone-500">
          {otherCount()} other task{otherCount() !== 1 ? "s" : ""}
        </p>
      </Show>
      <Show when={importantTasks().length === 0 && otherCount() === 0}>
        <p class="text-xs text-stone-500">No tasks</p>
      </Show>
    </div>
  );
};
