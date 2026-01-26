import { Component, Show, createMemo, createSignal, onCleanup, onMount } from "solid-js";
import { useNavigate } from "@solidjs/router";
import { Icon } from "@/components/shared/Icon";
import { faListCheck, faPlus } from "@fortawesome/free-solid-svg-icons";
import type { Task } from "@/types/api";
import TaskList from "@/components/tasks/List";
import {
  filterVisibleTasks,
  getTaskAvailableTime,
  getTaskDueByTime,
  isTaskAvailable,
} from "@/utils/tasks";

export interface TasksSectionProps {
  tasks: Task[];
  href: string;
}


export const TasksSection: Component<TasksSectionProps> = (props) => {
  const navigate = useNavigate();
  const [now, setNow] = createSignal(new Date());
  const [availableExpanded, setAvailableExpanded] = createSignal(false);

  onMount(() => {
    const interval = setInterval(() => {
      setNow(new Date());
    }, 30000);

    onCleanup(() => {
      clearInterval(interval);
    });
  });

  const visibleTasks = createMemo(() => filterVisibleTasks(props.tasks, now()));
  const activeTasks = createMemo(() =>
    visibleTasks().filter((t) => t.status !== "COMPLETE" && t.status !== "PUNT")
  );

  const importantTasks = createMemo(() =>
    activeTasks().filter((t) => t.tags?.includes("IMPORTANT"))
  );

  const adhocTasks = createMemo(() =>
    activeTasks().filter(
      (t) => t.type === "ADHOC" && !t.tags?.includes("IMPORTANT")
    )
  );

  const availableTasks = createMemo(() => {
    const currentTime = now();
    return activeTasks()
      .filter(
        (task) =>
          isTaskAvailable(task, currentTime) &&
          !task.tags?.includes("IMPORTANT") &&
          task.type !== "ADHOC"
      )
      .sort((a, b) => {
        const aDue = getTaskDueByTime(a);
        const bDue = getTaskDueByTime(b);
        if (aDue && bDue) {
          return aDue.getTime() - bDue.getTime();
        }
        const aAvailable = getTaskAvailableTime(a);
        const bAvailable = getTaskAvailableTime(b);
        if (!aAvailable || !bAvailable) return 0;
        return aAvailable.getTime() - bAvailable.getTime();
      });
  });

  const primaryTasks = createMemo(() => [
    ...importantTasks(),
    ...adhocTasks(),
  ]);

  return (
    <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
      <div class="flex items-center justify-between">
        <button
          type="button"
          onClick={() => navigate(props.href)}
          class="flex items-center gap-3 text-left"
          aria-label="See all tasks"
        >
          <Icon icon={faListCheck} class="w-5 h-5 fill-amber-600" />
          <p class="text-xs uppercase tracking-wide text-amber-700">Tasks</p>
        </button>
        <div class="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate("/me/adhoc-task")}
            class="inline-flex items-center justify-center w-9 h-9 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-600/80 transition hover:bg-amber-100/80 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Add adhoc task"
            title="Add adhoc task"
          >
            <Icon icon={faPlus} class="w-4 h-4 fill-amber-600/80" />
          </button>
        </div>
      </div>
      <Show when={primaryTasks().length > 0 || availableTasks().length > 0}>
        <div class="space-y-3">
          <Show when={primaryTasks().length > 0}>
            <div class="space-y-1">
              <TaskList tasks={primaryTasks} />
            </div>
          </Show>
          <Show when={availableTasks().length > 0}>
            <div class="border-t border-amber-100/80 pt-3">
              <button
                type="button"
                class="w-full flex items-center justify-between text-left"
                onClick={() => setAvailableExpanded(!availableExpanded())}
                aria-expanded={availableExpanded()}
              >
                <p class="text-[11px] uppercase tracking-wide text-amber-700">
                  Available
                </p>
                <span class="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700">
                  {availableTasks().length}
                </span>
              </button>
              <Show when={availableExpanded()}>
                <div class="mt-2 space-y-1">
                  <TaskList tasks={availableTasks} />
                </div>
              </Show>
            </div>
          </Show>
        </div>
      </Show>
    </div>
  );
};
