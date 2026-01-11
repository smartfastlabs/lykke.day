import Page from "@/components/shared/layout/Page";
import { Show, Component, createMemo, ParentProps } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import { Hero } from "@/components/overview";

export const HomeLayout: Component<ParentProps> = (props) => {
  const { dayContext, day, isLoading } = useSheppard();

  const date = createMemo(() => {
    const dayValue = day();
    return dayValue ? new Date(dayValue.date) : new Date();
  });

  const weekday = createMemo(() =>
    new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(date())
  );

  const monthDay = createMemo(() =>
    new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
    }).format(date())
  );

  const isWorkday = createMemo(() => {
    const dayValue = day();
    return Boolean(dayValue?.tags?.includes("WORKDAY"));
  });

  return (
    <Page>
      <Show
        when={!isLoading() && dayContext()}
        fallback={<div class="p-8 text-center text-gray-400">Loading...</div>}
      >
        <div class="relative min-h-screen overflow-hidden -mt-4 md:-mt-6">
          <div class="absolute inset-0 bg-gradient-to-br from-amber-50/60 via-orange-50/50 to-rose-50/50" />
          <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.12)_0%,_transparent_55%)]" />
          <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.08)_0%,_transparent_55%)]" />
          <div class="absolute top-24 right-10 w-44 h-44 bg-amber-200/25 rounded-full blur-3xl" />
          <div class="absolute bottom-20 left-8 w-36 h-36 bg-rose-200/20 rounded-full blur-3xl" />

          <div class="relative z-10 max-w-4xl mx-auto px-5 md:px-6 lg:px-8 py-8 md:py-10 space-y-6">
            <Hero
              weekday={weekday()}
              monthDay={monthDay()}
              isWorkday={isWorkday()}
              description="A balanced day ahead with a mix of focus work and personal tasks. You have a few meetings scheduled, but plenty of time for deep work in the morning. The afternoon looks lighter, perfect for catching up on tasks and taking a break."
            />
            {props.children}
          </div>
        </div>
      </Show>
    </Page>
  );
};

export default HomeLayout;
