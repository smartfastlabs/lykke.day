import { Component, For, Show } from "solid-js";
import type { Accessor } from "solid-js";
import { Goal, GoalStatus } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streaming-data";
import { SwipeableItem } from "@/components/shared/SwipeableItem";

const getStatusClasses = (status: GoalStatus): string => {
  switch (status) {
    case "COMPLETE":
      return "bg-stone-50/50";
    case "PUNT":
      return "bg-amber-50/30 italic";
    default:
      return "";
  }
};

const GoalItem: Component<{ goal: Goal }> = (props) => {
  const { updateGoalStatus, removeGoal } = useStreamingData();

  const handleSwipeLeft = () => {
    if (props.goal.status === "COMPLETE") {
      // If already complete, remove it on left swipe
      removeGoal(props.goal.id);
    } else {
      // Otherwise punt it
      updateGoalStatus(props.goal, "PUNT");
    }
  };

  return (
    <SwipeableItem
      onSwipeRight={() => updateGoalStatus(props.goal, "COMPLETE")}
      onSwipeLeft={handleSwipeLeft}
      rightLabel="✅ Complete Goal"
      leftLabel={props.goal.status === "COMPLETE" ? "🗑 Remove" : "⏸ Punt"}
      statusClass={getStatusClasses(props.goal.status)}
      compact={true}
    >
      <div class="flex items-center gap-4">
        {/* Goal icon */}
        <span class="w-4 flex-shrink-0 flex items-center justify-center text-amber-600">
          <span class="text-lg">🎯</span>
        </span>

        {/* Goal name */}
        <div class="flex-1 min-w-0">
          <span
            class={`text-sm truncate block ${
              props.goal.status === "COMPLETE"
                ? "line-through text-stone-400"
                : "text-stone-800"
            }`}
          >
            {props.goal.name}
          </span>
        </div>

        <Show when={props.goal.status === "COMPLETE"}>
          <div class="flex-shrink-0 w-4 text-amber-600">
            <Icon key="checkMark" />
          </div>
        </Show>
      </div>
    </SwipeableItem>
  );
};

interface GoalListProps {
  goals: Accessor<Goal[]>;
}

const GoalList: Component<GoalListProps> = (props) => {
  const goals = () => props.goals() ?? [];

  return (
    <>
      <For each={goals()}>{(goal) => <GoalItem goal={goal} />}</For>
    </>
  );
};

export default GoalList;
