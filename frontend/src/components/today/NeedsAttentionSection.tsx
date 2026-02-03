import { Component, Show, createMemo } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faTriangleExclamation } from "@fortawesome/free-solid-svg-icons";
import type { Task } from "@/types/api";
import TaskList from "@/components/tasks/List";
import { FuzzyCard, FuzzyLine } from "./FuzzyCard";

export interface NeedsAttentionSectionProps {
  tasks: Task[];
  isLoading?: boolean;
}

export const NeedsAttentionSection: Component<NeedsAttentionSectionProps> = (
  props,
) => {
  const needsAttentionTasks = createMemo(() =>
    props.tasks.filter(
      (task) =>
        task.timing_status === "needs_attention" &&
        task.status !== "COMPLETE" &&
        task.status !== "PUNT",
    ),
  );

  return (
    <Show
      when={!props.isLoading || props.tasks.length > 0}
      fallback={
        <FuzzyCard class="p-3 space-y-3">
          <div class="flex items-center gap-2">
            <div class="h-3 w-3 rounded-full bg-rose-200/90" />
            <FuzzyLine class="h-2 w-28" />
          </div>
          <div class="space-y-2">
            <FuzzyLine class="h-3 w-full" />
            <FuzzyLine class="h-3 w-4/5" />
            <FuzzyLine class="h-3 w-3/5" />
          </div>
        </FuzzyCard>
      }
    >
      <Show when={needsAttentionTasks().length > 0}>
        <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-3 backdrop-blur-sm space-y-2">
          <div class="flex items-center gap-2">
            <Icon icon={faTriangleExclamation} class="w-3 h-3 fill-rose-600" />
            <p class="text-[10px] uppercase tracking-wide text-rose-700">
              Needs attention
            </p>
          </div>

          <div class="space-y-1">
            <TaskList tasks={() => needsAttentionTasks()} />
          </div>
        </div>
      </Show>
    </Show>
  );
};
