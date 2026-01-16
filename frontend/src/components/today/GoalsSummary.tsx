import { Component, Show, createMemo } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faBullseye } from "@fortawesome/free-solid-svg-icons";
import type { Goal } from "@/types/api";
import GoalList from "@/components/goals/List";

export interface GoalsSummaryProps {
  goals: Goal[];
}

export const GoalsSummary: Component<GoalsSummaryProps> = (props) => {
  const hasGoals = createMemo(() => props.goals.length > 0);

  return (
    <Show when={hasGoals()}>
      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-6 backdrop-blur-sm">
        <div class="flex items-center gap-3 mb-5">
          <Icon icon={faBullseye} class="w-5 h-5 fill-amber-600" />
          <h3 class="text-lg font-semibold text-stone-800">Goals</h3>
        </div>

        <div class="space-y-0">
          <GoalList goals={() => props.goals} />
        </div>
      </div>
    </Show>
  );
};
