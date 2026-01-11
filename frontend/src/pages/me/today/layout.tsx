import Page from "@/components/shared/layout/Page";
import { Show, Component, createMemo, ParentProps } from "solid-js";
import { useSheppard } from "@/providers/sheppard";

export const TodayPageLayout: Component<ParentProps> = (props) => {
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
        fallback={<div class="p-8 text-center text-stone-400">Loading...</div>}
      >
        <div class="max-w-4xl mx-auto px-5 md:px-6 lg:px-8 py-8 md:py-10 space-y-6">
          {props.children}
        </div>
      </Show>
    </Page>
  );
};

export default TodayPageLayout;
