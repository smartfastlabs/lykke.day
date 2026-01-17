import { Component, Show, createMemo, createSignal } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faBullseye } from "@fortawesome/free-solid-svg-icons";
import type { Goal } from "@/types/api";
import GoalList from "@/components/goals/List";
import { useStreamingData } from "@/providers/streaming-data";

export interface GoalsSummaryProps {
  goals: Goal[];
}

export const GoalsSummary: Component<GoalsSummaryProps> = (props) => {
  const { addGoal, isLoading } = useStreamingData();
  const [newGoalName, setNewGoalName] = createSignal("");
  const [isAdding, setIsAdding] = createSignal(false);

  // Filter out completed and punted goals - only show active (INCOMPLETE) goals
  const activeGoals = createMemo(() =>
    props.goals.filter((g) => g.status === "INCOMPLETE")
  );

  const hasActiveGoals = createMemo(() => activeGoals().length > 0);
  const canAddGoal = createMemo(() => activeGoals().length < 3);

  const handleAddGoal = async () => {
    const name = newGoalName().trim();
    if (!name || isAdding() || !canAddGoal()) return;

    setIsAdding(true);
    try {
      await addGoal(name);
      setNewGoalName("");
    } catch (error) {
      console.error("Failed to add goal:", error);
    } finally {
      setIsAdding(false);
    }
  };

  const handleKeyPress = (e: globalThis.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAddGoal();
    }
  };

  return (
    <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-6 backdrop-blur-sm">
      <div class="flex items-center gap-3 mb-5">
        <Icon icon={faBullseye} class="w-5 h-5 fill-amber-600" />
        <h3 class="text-lg font-semibold text-stone-800">Goals</h3>
      </div>

      <Show when={hasActiveGoals()}>
        <div class="space-y-0 mb-4">
          <GoalList goals={activeGoals} />
        </div>
      </Show>

      <Show when={canAddGoal()}>
        <div class={hasActiveGoals() ? "pt-2 border-t border-stone-200/50" : ""}>
          <div class="flex gap-2">
            <input
              type="text"
              value={newGoalName()}
              onInput={(e) => setNewGoalName(e.currentTarget.value)}
              onKeyPress={handleKeyPress}
              placeholder="Add a goal..."
              disabled={isAdding() || isLoading()}
              class="flex-1 px-3 py-2 text-sm bg-white/80 border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed placeholder:text-stone-400"
            />
            <button
              onClick={handleAddGoal}
              disabled={!newGoalName().trim() || isAdding() || isLoading()}
              class="w-9 h-9 flex items-center justify-center bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-amber-500"
              aria-label="Add goal"
            >
              <Icon key="plus" class="w-4 h-4 fill-white" />
            </button>
          </div>
        </div>
      </Show>
    </div>
  );
};
