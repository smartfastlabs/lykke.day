import { Component, Show, createMemo } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faTriangleExclamation } from "@fortawesome/free-solid-svg-icons";
import type { Task } from "@/types/api";
import TaskList from "@/components/tasks/List";

export interface NeedsAttentionSectionProps {
  tasks: Task[];
}

export const NeedsAttentionSection: Component<NeedsAttentionSectionProps> = (
  props,
) => {
  const needsAttentionTasks = createMemo(() =>
    props.tasks.filter((task) => task.timing_status === "needs_attention"),
  );

  return (
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
  );
};
