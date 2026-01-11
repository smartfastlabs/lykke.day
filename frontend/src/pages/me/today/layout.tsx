import Page from "@/components/shared/layout/Page";
import { Show, Component, ParentProps, createMemo } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import { useLocation } from "@solidjs/router";

export const TodayPageLayout: Component<ParentProps> = (props) => {
  const { dayContext, isLoading, day } = useSheppard();
  const location = useLocation();

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
      <div class="min-h-screen relative overflow-hidden">
        <Show
          when={!isLoading() && dayContext()}
          fallback={
            <div class="relative z-10 p-8 text-center text-stone-400">
              Loading...
            </div>
          }
        >
          <div class="relative z-10 max-w-4xl mx-auto px-6 py-12 md:py-16">
            <div class="mb-8 md:mb-12">
              <div class="relative flex items-start justify-between">
                <div>
                  <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80 mb-2">
                    {weekday()} {monthDay()}
                  </p>
                </div>
                <Show when={isWorkday()}>
                  <span class="px-3 py-1.25 md:px-4 md:py-1.5 rounded-full bg-amber-50/95 text-amber-600 text-[11px] md:text-xs font-semibold uppercase tracking-wide border border-amber-100/80 shadow-sm shadow-amber-900/5">
                    Workday
                  </span>
                </Show>
              </div>
            </div>
            {props.children}
          </div>
        </Show>
      </div>
    </Page>
  );
};

export default TodayPageLayout;
