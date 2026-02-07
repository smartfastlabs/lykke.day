import { Component, createMemo } from "solid-js";
import { useStreamingData } from "@/providers/streamingData";
import AlarmList from "@/components/alarms/List";
import { AnimatedSection } from "@/components/shared/AnimatedSection";
import { SectionCard } from "@/components/shared/SectionCard";
import { MotivationalQuote } from "@/components/shared/MotivationalQuote";
import type { Alarm } from "@/types/api";

export const TodaysAlarmsView: Component = () => {
  const { dayContext } = useStreamingData();

  // Important: `useStreamingData().alarms()` hides CANCELLED + outdated (past)
  // alarms for the main `/me/today` experience. On the alarms page we want to
  // show the full list (including already-triggered/dismissed alarms), so we
  // use the raw day data instead.
  const alarms = createMemo<Alarm[]>(() => {
    const day = dayContext()?.day as unknown as
      | { alarms?: Alarm[] }
      | undefined;
    return day?.alarms ?? [];
  });

  const emptyState = <></>;

  return (
    <div class="w-full">
      <AnimatedSection delay="200ms">
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
