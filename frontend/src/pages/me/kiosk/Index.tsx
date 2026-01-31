import {
  Component,
  Show,
  createMemo,
  createSignal,
  onCleanup,
  onMount,
} from "solid-js";
import { Portal } from "solid-js/web";
import { KioskList } from "@/components/kiosk/KioskList";
import { KioskPanel } from "@/components/kiosk/KioskPanel";
import { useAlarmVideo } from "@/features/kiosk/alarms/useAlarmVideo";
import {
  formatClock,
  formatEventTime,
  formatRoutineTiming,
  getTaskTimeLabel,
  isAllDayEvent,
  type KioskItem,
} from "@/features/kiosk/kioskUtils";
import { useWeatherSnapshot } from "@/features/kiosk/weather/useWeatherSnapshot";
import Page from "@/components/shared/layout/Page";
import { useStreamingData } from "@/providers/streamingData";
import { getDateString } from "@/utils/dates";
import { filterVisibleTasks } from "@/utils/tasks";
import { buildRoutineGroups } from "@/components/routines/RoutineGroupsList";
import type { DayTemplate, Task } from "@/types/api";

type TimeBlock = NonNullable<DayTemplate["time_blocks"]>[number];

const KioskPage: Component = () => {
  const {
    dayContext,
    isLoading,
    day,
    tasks,
    events,
    reminders,
    routines,
    alarms,
    isConnected,
  } = useStreamingData();
  const [now, setNow] = createSignal(new Date());
  const { weather, weatherError } = useWeatherSnapshot();
  const { activeAlarm, alarmVideoUrl, setFullscreenContainerRef } =
    useAlarmVideo(alarms);

  onMount(() => {
    const interval = window.setInterval(() => {
      setNow(new Date());
    }, 30000);

    onCleanup(() => {
      window.clearInterval(interval);
    });
  });

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
    new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
    }).format(date()),
  );

  const dateLabel = createMemo(() => `${weekday()} ${monthDay()}`);
  const planTitle = createMemo(
    () => day()?.high_level_plan?.title?.trim() ?? "",
  );
  const isWorkday = createMemo(() => Boolean(day()?.tags?.includes("WORKDAY")));
  const timeBlocks = createMemo<TimeBlock[]>(
    () => day()?.template?.time_blocks ?? [],
  );
  const dayDate = createMemo(() => day()?.date ?? getDateString());
  const isToday = createMemo(() => dayDate() === getDateString());

  const blocks = createMemo(() =>
    timeBlocks()
      .map((block) => {
        const start =
          Number(block.start_time.slice(0, 2)) * 60 +
          Number(block.start_time.slice(3, 5));
        const end = Math.max(
          Number(block.end_time.slice(0, 2)) * 60 +
            Number(block.end_time.slice(3, 5)),
          start + 1,
        );
        return { ...block, start, end };
      })
      .sort((a, b) => a.start - b.start),
  );

  const currentBlock = createMemo(() => {
    if (!isToday()) return null;
    const nowMinutes = now().getHours() * 60 + now().getMinutes();
    return blocks().find(
      (block) => nowMinutes >= block.start && nowMinutes < block.end,
    );
  });

  const nextBlock = createMemo(() => {
    const items = blocks();
    if (items.length === 0) return null;
    if (!isToday()) return items[0];
    const nowMinutes = now().getHours() * 60 + now().getMinutes();
    return items.find((block) => block.start > nowMinutes) ?? null;
  });

  const allTasks = createMemo(() => tasks() ?? []);
  const allEvents = createMemo(() => events() ?? []);
  const allReminders = createMemo(() => reminders() ?? []);
  const allRoutines = createMemo(() => routines() ?? []);
  const activeReminders = createMemo(() =>
    allReminders().filter(
      (reminder) =>
        reminder.status !== "COMPLETE" && reminder.status !== "PUNT",
    ),
  );
  const visibleTasks = createMemo(() => filterVisibleTasks(allTasks()));
  const activeTasks = createMemo(() =>
    visibleTasks().filter(
      (task) => task.status !== "COMPLETE" && task.status !== "PUNT",
    ),
  );
  const upcomingTaskCandidates = createMemo(() =>
    allTasks().filter((task) => task.timing_status === "inactive"),
  );

  const rightNowEventIds = createMemo(() => {
    const currentTime = now();
    return new Set(
      allEvents()
        .filter((event) => {
          if (isAllDayEvent(event)) return false;
          const start = new Date(event.starts_at);
          const end = event.ends_at ? new Date(event.ends_at) : null;
          return start <= currentTime && (!end || end >= currentTime);
        })
        .map((event) => event.id)
        .filter((id): id is string => Boolean(id)),
    );
  });

  const upcomingEventIds = createMemo(() => {
    const currentTime = now();
    const windowEnd = new Date(currentTime.getTime() + 1000 * 30 * 60);
    return new Set(
      allEvents()
        .filter((event) => {
          if (isAllDayEvent(event)) return false;
          const start = new Date(event.starts_at);
          const end = event.ends_at ? new Date(event.ends_at) : null;
          if (start <= currentTime && (!end || end >= currentTime)) {
            return false;
          }
          return start >= currentTime && start <= windowEnd;
        })
        .map((event) => event.id)
        .filter((id): id is string => Boolean(id)),
    );
  });

  const rightNowTaskIds = createMemo(() => {
    return new Set(
      activeTasks()
        .filter((task) => task.timing_status === "past-due")
        .map((task) => task.id)
        .filter((id): id is string => Boolean(id)),
    );
  });

  const upcomingTaskIds = createMemo(() => {
    return new Set(
      upcomingTaskCandidates()
        .map((task) => task.id)
        .filter((id): id is string => Boolean(id)),
    );
  });

  const eventsForSections = createMemo(() => {
    const ids = new Set<string>();
    rightNowEventIds().forEach((id) => ids.add(id));
    upcomingEventIds().forEach((id) => ids.add(id));
    return allEvents().filter((event) => {
      const eventId = event.id;
      if (!eventId) return true;
      return !ids.has(eventId);
    });
  });

  const tasksForSections = createMemo(() => {
    const ids = new Set<string>();
    rightNowTaskIds().forEach((id) => ids.add(id));
    upcomingTaskIds().forEach((id) => ids.add(id));
    return filterVisibleTasks(allTasks()).filter((task) => {
      const taskId = task.id;
      if (!taskId) return true;
      if (ids.has(taskId)) return false;
      return true;
    });
  });

  const rightNowItems = createMemo<KioskItem[]>(() => {
    const items: KioskItem[] = [];
    const currentTime = now();

    allEvents()
      .filter((event) => {
        if (isAllDayEvent(event)) return false;
        const start = new Date(event.starts_at);
        const end = event.ends_at ? new Date(event.ends_at) : null;
        return start <= currentTime && (!end || end >= currentTime);
      })
      .forEach((event) => {
        items.push({
          label: event.name ?? "Event",
          time: formatEventTime(event.starts_at),
          meta: "event",
        });
      });

    activeTasks()
      .filter((task) => task.timing_status === "past-due")
      .forEach((task) => {
        items.push({
          label: task.name
            .replace("ROUTINE DEFINITION: ", "")
            .replace("Routine Definition: ", ""),
          time: getTaskTimeLabel(task),
          meta: "task",
        });
      });

    return items;
  });

  const upcomingItems = createMemo<KioskItem[]>(() => {
    const items: KioskItem[] = [];
    const currentTime = now();
    const windowEnd = new Date(currentTime.getTime() + 1000 * 30 * 60);

    allEvents()
      .filter((event) => {
        if (isAllDayEvent(event)) return false;
        const start = new Date(event.starts_at);
        if (start < currentTime || start > windowEnd) return false;
        return true;
      })
      .forEach((event) => {
        items.push({
          label: event.name ?? "Event",
          time: formatEventTime(event.starts_at),
          meta: "event",
        });
      });

    upcomingTaskCandidates().forEach((task) => {
      items.push({
        label: task.name
          .replace("ROUTINE DEFINITION: ", "")
          .replace("Routine Definition: ", ""),
        time: getTaskTimeLabel(task),
        meta: "task",
      });
    });

    return items;
  });

  const eventItems = createMemo<KioskItem[]>(() => {
    const items = eventsForSections()
      .slice()
      .sort(
        (a, b) =>
          new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
      )
      .map((event) => ({
        label: event.name ?? "Event",
        time: isAllDayEvent(event)
          ? "all day"
          : formatEventTime(event.starts_at),
        meta: event.category?.toLowerCase().replace("_", " "),
      }));

    return items;
  });

  const taskItems = createMemo<KioskItem[]>(() =>
    tasksForSections()
      .filter((task) => task.status !== "COMPLETE" && task.status !== "PUNT")
      .map((task) => ({
        label: task.name
          .replace("ROUTINE DEFINITION: ", "")
          .replace("Routine Definition: ", ""),
        time: getTaskTimeLabel(task),
        meta: task.type?.toLowerCase().replace("_", " "),
      })),
  );

  const reminderItems = createMemo<KioskItem[]>(() =>
    activeReminders().map((reminder: Task) => ({
      label: reminder.name,
      meta: "reminder",
    })),
  );

  const routineItems = createMemo<KioskItem[]>(() => {
    const groups = buildRoutineGroups(activeTasks(), allRoutines());
    return groups.map((group) => ({
      label: group.routineName ?? "Routine",
      time: formatRoutineTiming(group),
      meta: `${group.pendingCount}/${group.totalCount}`,
    }));
  });

  const timeLabel = createMemo(() => formatClock(now()));

  return (
    <Page variant="app" hideFooter hideFloatingButtons>
      <div class="min-h-[100dvh] h-[100dvh] box-border relative overflow-hidden">
        {activeAlarm() && alarmVideoUrl() ? (
          <Portal>
            <div
              ref={setFullscreenContainerRef}
              class="fixed inset-0 z-[90] bg-black"
            >
              <iframe
                class="h-full w-full"
                src={alarmVideoUrl() ?? ""}
                title={activeAlarm()?.name ?? "Alarm Video"}
                allow="autoplay; fullscreen"
                allowfullscreen
              />
            </div>
          </Portal>
        ) : null}
        {!isLoading() && dayContext() ? (
          <div class="relative z-10 h-full w-full">
            <div class="h-full w-full flex flex-col gap-3 p-[25px]">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm uppercase tracking-[0.3em] text-stone-500">
                    {dateLabel()}
                  </p>
                  <p class="text-2xl font-semibold text-stone-800">
                    {planTitle() || "Today"}
                  </p>
                  <div class="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-stone-500">
                    <span
                      class={
                        isConnected()
                          ? "rounded-full bg-emerald-50 px-2 py-0.5 font-semibold text-emerald-700"
                          : "rounded-full bg-rose-50 px-2 py-0.5 font-semibold text-rose-700"
                      }
                    >
                      {isConnected() ? "WS connected" : "WS disconnected"}
                    </span>
                  </div>
                </div>
              </div>
              <div class="flex-1 min-h-0 grid grid-cols-3 grid-rows-2 gap-3">
                <KioskPanel title="Now" count={rightNowItems().length}>
                  <div class="space-y-3">
                    <div class="flex items-end justify-between">
                      <div class="text-4xl font-semibold text-amber-700 tabular-nums">
                        {timeLabel()}
                      </div>
                    </div>
                    <Show when={isWorkday()}>
                      <span class="inline-flex items-center rounded-full bg-amber-50/95 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-amber-600 shadow-sm shadow-amber-900/5">
                        Workday
                      </span>
                    </Show>
                    <div class="flex items-center justify-between rounded-xl bg-white/70 px-3 py-2 text-sm text-stone-700">
                      <div>
                        <p class="text-[11px] uppercase tracking-[0.2em] text-stone-400">
                          Weather
                        </p>
                        <Show
                          when={weather()}
                          fallback={
                            <p class="text-sm text-stone-500">
                              {weatherError() ? "Unavailable" : "Loading..."}
                            </p>
                          }
                        >
                          {(snapshot) => (
                            <p class="text-base font-semibold text-stone-800">
                              {snapshot().temperature}°F ·{" "}
                              {snapshot().condition}
                            </p>
                          )}
                        </Show>
                      </div>
                      <div class="text-2xl">⛅️</div>
                    </div>
                    <Show when={blocks().length > 0}>
                      <div class="text-[11px] text-stone-500">
                        <Show
                          when={currentBlock()}
                          fallback={
                            <span>
                              <span class="font-medium">Current:</span> none
                            </span>
                          }
                        >
                          {(block) => (
                            <span>
                              <span class="font-medium">Current:</span>{" "}
                              {block().name}
                            </span>
                          )}
                        </Show>
                        <span class="mx-2 text-stone-300">•</span>
                        <Show
                          when={nextBlock()}
                          fallback={
                            <span>
                              <span class="font-medium">Next:</span> none
                            </span>
                          }
                        >
                          {(block) => (
                            <span>
                              <span class="font-medium">Next:</span>{" "}
                              {block().name}
                            </span>
                          )}
                        </Show>
                      </div>
                    </Show>
                    <KioskList
                      items={rightNowItems()}
                      emptyLabel="active items"
                    />
                  </div>
                </KioskPanel>
                <KioskPanel
                  title="Upcoming (30m)"
                  count={upcomingItems().length}
                >
                  <KioskList
                    items={upcomingItems()}
                    emptyLabel="upcoming items"
                  />
                </KioskPanel>
                <KioskPanel title="Reminders" count={activeReminders().length}>
                  <KioskList items={reminderItems()} emptyLabel="reminders" />
                </KioskPanel>
                <KioskPanel title="Events" count={eventItems().length}>
                  <KioskList items={eventItems()} emptyLabel="events" />
                </KioskPanel>
                <KioskPanel title="Tasks" count={taskItems().length}>
                  <KioskList items={taskItems()} emptyLabel="tasks" />
                </KioskPanel>
                <KioskPanel title="Routines" count={routineItems().length}>
                  <KioskList items={routineItems()} emptyLabel="routines" />
                </KioskPanel>
              </div>
            </div>
          </div>
        ) : (
          <div class="relative z-10 p-8 text-center text-stone-400">
            Loading...
          </div>
        )}
      </div>
    </Page>
  );
};

export default KioskPage;
