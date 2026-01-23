import { Component, Show, createMemo } from "solid-js";
import { useNavigate } from "@solidjs/router";
import { Icon } from "@/components/shared/Icon";
import { faListCheck, faPlus } from "@fortawesome/free-solid-svg-icons";
import type { Task } from "@/types/api";
import TaskList from "@/components/tasks/List";

export interface TasksSectionProps {
  tasks: Task[];
  href: string;
}


export const TasksSection: Component<TasksSectionProps> = (props) => {
  const navigate = useNavigate();
  const activeTasks = createMemo(() =>
    props.tasks.filter((t) => t.status !== "COMPLETE" && t.status !== "PUNT")
  );

  const importantTasks = createMemo(() =>
    activeTasks().filter((t) => t.tags?.includes("IMPORTANT"))
  );

  const adhocTasks = createMemo(() =>
    activeTasks().filter(
      (t) => t.type === "ADHOC" && !t.tags?.includes("IMPORTANT")
    )
  );

  const displayedTasks = createMemo(() => [
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
      <Show when={displayedTasks().length > 0}>
        <div class="space-y-1">
          <TaskList tasks={displayedTasks} />
        </div>
      </Show>
    </div>
  );
};
