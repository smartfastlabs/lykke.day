import { faRotate } from "@fortawesome/free-solid-svg-icons";
import {
  Component,
  ParentProps,
  Show,
  createMemo,
  createSignal,
} from "solid-js";
import Page from "@/components/shared/layout/Page";
import { Icon } from "@/components/shared/Icon";
import {
  TomorrowDataProvider,
  useTomorrowData,
} from "@/pages/me/tomorrow/useTomorrowData";
import { tomorrowAPI } from "@/utils/api";

const TomorrowPageLayoutInner: Component<ParentProps> = (props) => {
  const { day, isDayLoading, refetchAll } = useTomorrowData();
  const [isRescheduling, setIsRescheduling] = createSignal(false);

  const date = createMemo(() => {
    const dayValue = day();
    if (!dayValue) return new Date();
    const [year, month, dayNum] = dayValue.date.split("-").map(Number);
    return new Date(year, month - 1, dayNum);
  });

  const weekday = createMemo(() =>
    new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(date()),
  );

  const monthDay = createMemo(() =>
    new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric" }).format(
      date(),
    ),
  );

  const dateLabel = createMemo(() => `${weekday()} ${monthDay()}`);

  return (
    <Page variant="app" hideFooter>
      <div class="min-h-[100dvh] box-border relative overflow-hidden">
        <Show
          when={!isDayLoading() && day()}
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
                      Tomorrow
                    </span>
                  </div>
                  <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
                    {dateLabel()}
                  </p>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={async () => {
                      if (isRescheduling()) return;
                      try {
                        setIsRescheduling(true);
                        await tomorrowAPI.reschedule();
                        refetchAll();
                      } finally {
                        setIsRescheduling(false);
                      }
                    }}
                    aria-label="Reschedule"
                    title="Reschedule"
                    class="inline-flex items-center gap-2 px-3 py-2 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-700/80 transition hover:bg-amber-100/80 hover:text-amber-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isRescheduling()}
                  >
                    <Icon icon={faRotate} class="w-4 h-4 fill-amber-600/70" />
                    <span class="text-xs font-semibold">
                      {isRescheduling() ? "Rescheduling…" : "Reschedule"}
                    </span>
                  </button>
                </div>
              </div>
            </div>
            {props.children}
          </div>
        </Show>
      </div>
    </Page>
  );
};

export const TomorrowPageLayout: Component<ParentProps> = (props) => {
  return (
    <TomorrowDataProvider>
      <TomorrowPageLayoutInner>{props.children}</TomorrowPageLayoutInner>
    </TomorrowDataProvider>
  );
};

export default TomorrowPageLayout;
