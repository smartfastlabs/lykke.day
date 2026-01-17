import { faRotate } from "@fortawesome/free-solid-svg-icons";
import { Show, Component, ParentProps, createMemo } from "solid-js";
import Page from "@/components/shared/layout/Page";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streaming-data";
import TimeBlocksSummary from "@/components/today/TimeBlocksSummary";

export const TodayPageLayout: Component<ParentProps> = (props) => {
  const { dayContext, isLoading, day, sync } = useStreamingData();

  const date = createMemo(() => {
    const dayValue = day();
    if (!dayValue) return new Date();

    // Parse date string as local date to avoid timezone issues
    // e.g., "2026-01-15" should be Jan 15 in local time, not UTC midnight
    const [year, month, dayNum] = dayValue.date.split("-").map(Number);
    return new Date(year, month - 1, dayNum); // month is 0-indexed
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

  const timeBlocks = createMemo(() => day()?.template?.time_blocks ?? []);
  const dayDate = createMemo(() => day()?.date);

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
          <div class="relative z-10 max-w-4xl mx-auto px-6 py-6">
            <div class="mb-8 md:mb-12">
              <div class="relative flex items-start justify-between mb-4">
                <div>
                  <p class="text-lg uppercase tracking-[0.2em] text-amber-600/80 mb-2">
                    {weekday()} {monthDay()}
                  </p>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={sync}
                    aria-label="Refresh"
                    title="Refresh"
                    class="p-2 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-600/70 transition hover:bg-amber-100/80 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200"
                  >
                    <Icon icon={faRotate} class="w-4 h-4 fill-amber-600/70" />
                  </button>
                  <Show when={isWorkday()}>
                    <span class="px-3 py-1.25 md:px-4 md:py-1.5 rounded-full bg-amber-50/95 text-amber-600 text-[11px] md:text-xs font-semibold uppercase tracking-wide border border-amber-100/80 shadow-sm shadow-amber-900/5">
                      Workday
                    </span>
                  </Show>
                </div>
              </div>
              <TimeBlocksSummary timeBlocks={timeBlocks()} dayDate={dayDate()} />
            </div>
            {props.children}
          </div>
        </Show>
      </div>
    </Page>
  );
};

export default TodayPageLayout;
