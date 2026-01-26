import { Component, createMemo } from "solid-js";
import { useStreamingData } from "@/providers/streamingData";
import AlarmList from "@/components/alarms/List";
import { AnimatedSection } from "@/components/shared/AnimatedSection";
import { StatsCard } from "@/components/shared/StatsCard";
import { SectionCard } from "@/components/shared/SectionCard";
import { MotivationalQuote } from "@/components/shared/MotivationalQuote";

const getAlarmStats = (alarms: { url?: string }[]) => {
  const total = alarms.length;
  const withLinks = alarms.filter((alarm) => Boolean(alarm.url)).length;
  return { total, withLinks };
};

export const TodaysAlarmsView: Component = () => {
  const { alarms } = useStreamingData();

  const stats = createMemo(() => getAlarmStats(alarms()));
  const completionPercentage = createMemo(() => {
    const s = stats();
    return s.total > 0 ? Math.round((s.withLinks / s.total) * 100) : 0;
  });
  const statItems = createMemo(() => [
    { label: "Total", value: stats().total },
    {
      label: "With Links",
      value: stats().withLinks,
      colorClasses:
        "bg-gradient-to-br from-amber-50 to-orange-50 border-amber-100 text-amber-700",
    },
  ]);

  const emptyState = <></>;

  return (
    <div class="w-full">
      <AnimatedSection delay="200ms">
        <div class="mb-8">
          <StatsCard
            title="Today's Alarms"
            completionPercentage={completionPercentage}
            stats={statItems}
          />
        </div>
      </AnimatedSection>

      <AnimatedSection delay="300ms">
        <SectionCard
          title="Your Alarms"
          description="Plan your day with intentional cues."
          hasItems={alarms().length > 0}
          emptyState={emptyState}
        >
          <AlarmList alarms={alarms} />
        </SectionCard>
      </AnimatedSection>

      <AnimatedSection delay="500ms">
        <MotivationalQuote
          quote="Make the important cues obvious, and the important moments follow."
          author="Unknown"
        />
      </AnimatedSection>
    </div>
  );
};

export default TodaysAlarmsView;
