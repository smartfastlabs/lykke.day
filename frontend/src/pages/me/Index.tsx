import { Component, Show, createMemo, createSignal, type ParentProps } from "solid-js";

import { useStreamingData } from "@/providers/streamingData";
import TodayPageLayout from "@/pages/me/today/Layout";
import TodayIndexView from "@/pages/me/today/Index";
import ThatsAllPage from "@/pages/me/today/ThatsAll";
import { dayAPI } from "@/utils/api";

type DayStatus = import("@/types/api").components["schemas"]["DayStatus"];

const StatusCard: Component<{
  eyebrow: string;
  title: string;
  description: string;
} & ParentProps> = (props) => {
  return (
    <div class="max-w-2xl">
      <div class="rounded-2xl border border-amber-100/80 bg-white/70 shadow-lg shadow-amber-900/5 backdrop-blur-sm p-5 space-y-4">
        <div>
          <p class="text-[11px] uppercase tracking-wide text-amber-700">
            {props.eyebrow}
          </p>
          <h2 class="text-lg font-medium text-stone-900">{props.title}</h2>
          <p class="text-sm text-stone-500">{props.description}</p>
        </div>
        {props.children}
      </div>
    </div>
  );
};

export const MeIndexPage: Component = () => {
  const { day, tasks, events, routines, reminders, alarms, isLoading, sync } =
    useStreamingData();

  const status = createMemo<DayStatus | null>(() => day()?.status ?? null);
  const template = createMemo(() => day()?.template ?? null);

  const [isScheduling, setIsScheduling] = createSignal(false);
  const [scheduleError, setScheduleError] = createSignal<string | null>(null);

  const scheduleToday = async () => {
    const currentDay = day();
    if (!currentDay?.id) return;

    setScheduleError(null);
    setIsScheduling(true);
    try {
      await dayAPI.updateDay(currentDay.id, { status: "SCHEDULED" });
      sync();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to schedule today";
      setScheduleError(message);
    } finally {
      setIsScheduling(false);
    }
  };

  // COMPLETE is a "post day" experience that already has its own page layout.
  if (status() === "COMPLETE") {
    return <ThatsAllPage />;
  }

  // Use the exact same layout/theme as /me/today for everything else.
  return (
    <TodayPageLayout>
      <Show
        when={!isLoading() && Boolean(day())}
        fallback={
          <StatusCard
            eyebrow="Loading"
            title="Getting your day ready"
            description="One moment…"
          />
        }
      >
        <Show when={status() === "STARTED"}>
          <TodayIndexView />
        </Show>

        <Show when={status() === "SCHEDULED"}>
          <StatusCard
            eyebrow="Scheduled"
            title="Ready when you are"
            description="Your day is scheduled. Add a high-level plan to begin."
          >
            <div class="flex flex-col sm:flex-row gap-3">
              <a
                href="/me/today/edit"
                class="inline-flex items-center justify-center rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-700"
              >
                Set intentions (start)
              </a>
              <a
                href="/me/today"
                class="inline-flex items-center justify-center rounded-lg border border-amber-100/80 bg-amber-50/70 px-4 py-2 text-sm font-semibold text-amber-700 transition hover:bg-amber-100/80"
              >
                View dashboard
              </a>
            </div>
            <div class="pt-2 text-xs text-stone-500">
              <span class="font-semibold text-stone-600">Today snapshot:</span>{" "}
              {tasks().length} tasks, {events().length} events,{" "}
              {routines().length} routines, {reminders().length} reminders,{" "}
              {alarms().length} alarms
            </div>
          </StatusCard>
        </Show>

        <Show when={status() === "UNSCHEDULED"}>
          <StatusCard
            eyebrow="Unscheduled"
            title="Today isn’t scheduled yet"
            description="Pick a template and schedule your day."
          >
            <Show
              when={Boolean(template()?.id)}
              fallback={
                <div class="space-y-3">
                  <p class="text-sm text-stone-600">
                    No template is attached to today yet.
                  </p>
                  <a
                    href="/me/settings/day-templates"
                    class="inline-flex items-center justify-center rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-700"
                  >
                    Choose a template
                  </a>
                </div>
              }
            >
              <div class="space-y-3">
                <div class="flex flex-col sm:flex-row gap-3">
                  <button
                    type="button"
                    onClick={() => void scheduleToday()}
                    disabled={isScheduling()}
                    class="inline-flex items-center justify-center rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-700 disabled:opacity-60"
                  >
                    {isScheduling() ? "Scheduling…" : "Schedule today"}
                  </button>
                  <a
                    href="/me/settings/day-templates"
                    class="inline-flex items-center justify-center rounded-lg border border-amber-100/80 bg-amber-50/70 px-4 py-2 text-sm font-semibold text-amber-700 transition hover:bg-amber-100/80"
                  >
                    Change template
                  </a>
                </div>
                <Show when={scheduleError()}>
                  <p class="text-xs text-rose-600">{scheduleError()}</p>
                </Show>
              </div>
            </Show>
          </StatusCard>
        </Show>

        <Show when={!status()}>
          <StatusCard
            eyebrow="Welcome"
            title="Your day is loading"
            description="Hang tight while we sync."
          />
        </Show>
      </Show>
    </TodayPageLayout>
  );
};

export default MeIndexPage;
