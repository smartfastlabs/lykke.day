import { Component, createMemo } from "solid-js";
import { useStreamingData } from "@/providers/streamingData";
import ReminderList from "@/components/reminders/List";
import { Reminder } from "@/types/api";
import { AnimatedSection } from "@/components/shared/AnimatedSection";
import { StatsCard } from "@/components/shared/StatsCard";
import { SectionCard } from "@/components/shared/SectionCard";
import { MotivationalQuote } from "@/components/shared/MotivationalQuote";

const getReminderStats = (reminders: Reminder[]) => {
  const total = reminders.length;
  const incomplete = reminders.filter((r) => r.status === "INCOMPLETE").length;
  const completed = reminders.filter((r) => r.status === "COMPLETE").length;
  const punted = reminders.filter((r) => r.status === "PUNT").length;
  return { total, incomplete, completed, punted };
};

export const TodaysRemindersView: Component = () => {
  const { reminders } = useStreamingData();

  const stats = createMemo(() => getReminderStats(reminders()));
  const completionPercentage = createMemo(() => {
    const s = stats();
    return s.total > 0 ? Math.round((s.completed / s.total) * 100) : 0;
  });

  const statItems = createMemo(() => [
    { label: "Total", value: stats().total },
    {
      label: "Active",
      value: stats().incomplete,
      colorClasses:
        "bg-gradient-to-br from-amber-50 to-orange-50 border-amber-100 text-amber-700",
    },
    {
      label: "Done",
      value: stats().completed,
      colorClasses:
        "bg-gradient-to-br from-green-50 to-emerald-50 border-green-100 text-green-700",
    },
    {
      label: "Punted",
      value: stats().punted,
      colorClasses:
        "bg-gradient-to-br from-rose-50 to-red-50 border-rose-200 text-rose-700",
    },
  ]);

  const emptyState = (
    <div class="px-6 py-12 text-center">
      <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 mb-4">
        <span class="text-3xl">🎯</span>
      </div>
      <p class="text-stone-600 text-lg font-medium mb-2">No reminders for today</p>
      <p class="text-stone-500 text-sm">Stay focused and keep moving forward!</p>
    </div>
  );

  return (
    <div class="w-full">
      <AnimatedSection delay="200ms">
        <div class="mb-8">
          <StatsCard
            title="Today's Reminders"
            completionPercentage={completionPercentage}
            stats={statItems}
          />
        </div>
      </AnimatedSection>

      <AnimatedSection delay="300ms">
        <SectionCard
          title="Your Reminders"
          description="Swipe right to complete, left to punt"
          hasItems={reminders().length > 0}
          emptyState={emptyState}
        >
          <ReminderList reminders={reminders} />
        </SectionCard>
      </AnimatedSection>

      <AnimatedSection delay="500ms">
        <MotivationalQuote
          quote="The best way to remember something is to remind yourself of it. The best way to achieve something is to remind yourself why it matters."
          author="Unknown"
        />
      </AnimatedSection>
    </div>
  );
};

export default TodaysRemindersView;
