import { Component, createSignal, createMemo } from "solid-js";
import { useStreamingData } from "@/providers/streaming-data";
import GoalList from "@/components/goals/List";
import { Goal } from "@/types/api";
import { AnimatedSection } from "@/components/shared/AnimatedSection";
import { StatsCard } from "@/components/shared/StatsCard";
import { SectionCard } from "@/components/shared/SectionCard";
import { MotivationalQuote } from "@/components/shared/MotivationalQuote";

const getGoalStats = (goals: Goal[]) => {
  const total = goals.length;
  const completed = goals.filter((g) => g.status === "COMPLETE").length;
  const incomplete = goals.filter((g) => g.status === "INCOMPLETE").length;
  const punted = goals.filter((g) => g.status === "PUNT").length;
  return { total, completed, incomplete, punted };
};

export const TodaysGoalsView: Component = () => {
  const { goals, addGoal, isLoading } = useStreamingData();
  const [newGoalName, setNewGoalName] = createSignal("");
  const [isAdding, setIsAdding] = createSignal(false);

  const stats = createMemo(() => getGoalStats(goals()));
  const completionPercentage = createMemo(() => {
    const s = stats();
    return s.total > 0 ? Math.round((s.completed / s.total) * 100) : 0;
  });

  const statItems = createMemo(() => [
    { label: "Total", value: stats().total },
    {
      label: "Done",
      value: stats().completed,
      colorClasses:
        "bg-gradient-to-br from-green-50 to-emerald-50 border-green-100 text-green-700",
    },
    {
      label: "Active",
      value: stats().incomplete,
      colorClasses:
        "bg-gradient-to-br from-amber-50 to-orange-50 border-amber-100 text-amber-700",
    },
    {
      label: "Punted",
      value: stats().punted,
      colorClasses:
        "bg-gradient-to-br from-rose-50 to-red-50 border-rose-200 text-rose-700",
    },
  ]);

  const handleAddGoal = async () => {
    const name = newGoalName().trim();
    if (!name || isAdding()) return;

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

  const emptyState = (
    <div class="px-6 py-12 text-center">
      <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 mb-4">
        <span class="text-3xl">🎯</span>
      </div>
      <p class="text-stone-600 text-lg font-medium mb-2">No goals yet</p>
      <p class="text-stone-500 text-sm">
        Add your first goal above to get started!
      </p>
    </div>
  );

  return (
    <div class="w-full">
      <AnimatedSection delay="200ms">
        <div class="mb-8">
          <StatsCard
            title="Today's Goals"
            completionPercentage={completionPercentage}
            stats={statItems}
          />
        </div>
      </AnimatedSection>

      <AnimatedSection delay="300ms">
        <div class="mb-8">
          <div class="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl shadow-xl shadow-amber-900/5 p-6 md:p-8">
            <h3 class="text-lg font-semibold text-stone-800 mb-4">
              Add a Goal
            </h3>
            <div class="flex gap-3">
              <input
                type="text"
                value={newGoalName()}
                onInput={(e) => setNewGoalName(e.currentTarget.value)}
                onKeyPress={handleKeyPress}
                placeholder="What do you want to achieve today?"
                disabled={isAdding() || isLoading()}
                class="flex-1 px-4 py-3 bg-white/80 border border-stone-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <button
                onClick={handleAddGoal}
                disabled={!newGoalName().trim() || isAdding() || isLoading()}
                class="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white font-semibold rounded-xl hover:from-amber-600 hover:to-orange-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-amber-500 disabled:hover:to-orange-500"
              >
                {isAdding() ? "Adding..." : "Add"}
              </button>
            </div>
          </div>
        </div>
      </AnimatedSection>

      <AnimatedSection delay="400ms">
        <SectionCard
          title="Your Goals"
          description="Swipe right to complete, left to punt or remove"
          hasItems={goals().length > 0}
          emptyState={emptyState}
        >
          <GoalList goals={goals} />
        </SectionCard>
      </AnimatedSection>

      <AnimatedSection delay="500ms">
        <MotivationalQuote
          quote="A goal without a plan is just a wish."
          author="Antoine de Saint-Exupéry"
        />
      </AnimatedSection>
    </div>
  );
};

export default TodaysGoalsView;
