import { Component, createMemo, Show } from "solid-js";
import { useStreamingData } from "@/providers/streaming-data";
import TaskList from "@/components/tasks/List";
import { Task, TaskStatus } from "@/types/api";
import { AnimatedSection } from "@/components/shared/AnimatedSection";
import { StatsCard } from "@/components/shared/StatsCard";
import { SectionCard } from "@/components/shared/SectionCard";
import { MotivationalQuote } from "@/components/shared/MotivationalQuote";

const getTaskStats = (tasks: Task[]) => {
  const total = tasks.length;
  const completed = tasks.filter((t) => t.status === "COMPLETE").length;
  const pending = tasks.filter((t) => t.status === "PENDING").length;
  const punted = tasks.filter((t) => t.status === "PUNT").length;
  return { total, completed, pending, punted };
};

export const TodaysTasksView: Component = () => {
  const { tasks } = useStreamingData();

  const stats = createMemo(() => getTaskStats(tasks()));
  const completionPercentage = createMemo(() => {
    const s = stats();
    return s.total > 0 ? Math.round((s.completed / s.total) * 100) : 0;
  });

  const statItems = createMemo(() => [
    { label: "Total", value: stats().total },
    {
      label: "Completed",
      value: stats().completed,
      colorClasses: "bg-gradient-to-br from-green-50 to-emerald-50 border-green-100 text-green-700",
    },
    {
      label: "Pending",
      value: stats().pending,
      colorClasses: "bg-gradient-to-br from-amber-50 to-orange-50 border-amber-100 text-amber-700",
    },
    {
      label: "Punted",
      value: stats().punted,
      colorClasses: "bg-gradient-to-br from-rose-50 to-red-50 border-rose-200 text-rose-700",
    },
  ]);

  const emptyState = (
    <div class="px-6 py-12 text-center">
      <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 mb-4">
        <span class="text-3xl">✨</span>
      </div>
      <p class="text-stone-600 text-lg font-medium mb-2">
        No tasks for today
      </p>
      <p class="text-stone-500 text-sm">Enjoy your free time!</p>
    </div>
  );

  return (
    <div class="w-full">
      <AnimatedSection delay="200ms">
        <div class="mb-8">
          <StatsCard
            title="Today's Progress"
            completionPercentage={completionPercentage}
            stats={statItems}
          />
        </div>
      </AnimatedSection>

      <AnimatedSection delay="300ms">
        <SectionCard
          title="Your Tasks"
          description="Swipe right to complete, left to punt"
          hasItems={tasks().length > 0}
          emptyState={emptyState}
        >
          <TaskList tasks={tasks} />
        </SectionCard>
      </AnimatedSection>

      <AnimatedSection delay="500ms">
        <MotivationalQuote
          quote="The secret of getting ahead is getting started. The secret of getting started is breaking your complex overwhelming tasks into small manageable tasks."
          author="Mark Twain"
        />
      </AnimatedSection>
    </div>
  );
};

export default TodaysTasksView;
