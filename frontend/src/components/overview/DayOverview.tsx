import { Component, Show } from "solid-js";
import Page from "@/components/shared/layout/Page";
import { Hero, type HeroProps } from "./Hero";
import { ComingUpCard, type ComingUpCardProps } from "./ComingUpCard";
import { ReminderCard, type ReminderCardProps } from "./ReminderCard";
import { RoutinesCard, type RoutinesCardProps } from "./RoutinesCard";
import { FlowCard, type FlowCardProps } from "./FlowCard";

export interface DayOverviewProps {
  hero: HeroProps;
  comingUp?: ComingUpCardProps;
  reminder?: ReminderCardProps;
  routines?: RoutinesCardProps;
  flow?: FlowCardProps;
  withPageWrapper?: boolean;
}

export const DayOverview: Component<DayOverviewProps> = (props) => {
  const content = (
    <div class="relative min-h-screen overflow-hidden -mt-4 md:-mt-6">
      <div class="absolute inset-0 bg-gradient-to-br from-amber-50/60 via-orange-50/50 to-rose-50/50" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.12)_0%,_transparent_55%)]" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.08)_0%,_transparent_55%)]" />
      <div class="absolute top-24 right-10 w-44 h-44 bg-amber-200/25 rounded-full blur-3xl" />
      <div class="absolute bottom-20 left-8 w-36 h-36 bg-rose-200/20 rounded-full blur-3xl" />

      <div class="relative z-10 max-w-4xl mx-auto px-5 md:px-6 lg:px-8 py-8 md:py-10 space-y-6">
        <Hero {...props.hero} />

        <div class="grid md:grid-cols-3 gap-4 md:gap-6">
          <Show when={props.comingUp}>
            {(comingUp) => <ComingUpCard {...comingUp()} />}
          </Show>
          <Show when={props.reminder}>
            {(reminder) => <ReminderCard {...reminder()} />}
          </Show>
        </div>

        <div class="grid md:grid-cols-3 gap-4 md:gap-6">
          <Show when={props.routines}>
            {(routines) => <RoutinesCard {...routines()} />}
          </Show>
          <Show when={props.flow}>
            {(flow) => <FlowCard {...flow()} />}
          </Show>
        </div>
      </div>
    </div>
  );

  return (
    <Show when={props.withPageWrapper} fallback={content}>
      <Page>{content}</Page>
    </Show>
  );
};

