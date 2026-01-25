import { faPenToSquare, faRotate } from "@fortawesome/free-solid-svg-icons";
import { Show, Component, ParentProps, createMemo } from "solid-js";
import Page from "@/components/shared/layout/Page";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streamingData";
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

  const planTitle = createMemo(() => {
    const title = day()?.high_level_plan?.title ?? "";
    return title.trim();
  });

  const isWorkday = createMemo(() => {
    const dayValue = day();
    return Boolean(dayValue?.tags?.includes("WORKDAY"));
  });

  const timeBlocks = createMemo(() => day()?.template?.time_blocks ?? []);
  const dayDate = createMemo(() => day()?.date);

  const dateLabel = createMemo(() => `${weekday()} ${monthDay()}`);

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
            <div class="mb-5 md:mb-7">
              <div class="relative flex items-start justify-between mb-4">
                <div>
                  <div class="flex items-center gap-3 text-stone-600 mb-2">
                    <span class="font-semibold text-lg text-amber-600/80">
                      {planTitle() || dateLabel()}
                    </span>
                  </div>
                  <Show when={planTitle()}>
                    <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
                      {dateLabel()}
                    </p>
                  </Show>
                </div>
                <div class="flex items-center gap-2">
                  <a
                    href="/me/today/edit"
                    aria-label="Edit day"
                    title="Edit day"
                    class="p-2 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-600/70 transition hover:bg-amber-100/80 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200"
                  >
                    <Icon icon={faPenToSquare} class="w-4 h-4 fill-amber-600/70" />
                  </a>
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
