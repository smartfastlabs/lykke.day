import { Component, For, Show, createMemo } from "solid-js";
import {
  faBell,
  faCalendarDay,
  faCheckCircle,
  faDroplet,
  faLeaf,
  faMoon,
  faPersonRunning,
  faSun,
  faWater,
} from "@fortawesome/free-solid-svg-icons";

import Page from "@/components/shared/layout/Page";
import { Icon } from "@/components/shared/Icon";
import type { Day, Event, Routine, Task } from "@/types/api";

const today: Day = {
  id: "day-2026-01-08",
  user_id: "user-001",
  date: "2026-01-08",
  template_id: "template-calm",
  tags: ["WORKDAY"],
  alarm: {
    id: "alarm-morning",
    name: "Sunrise Wake",
    time: "07:00",
    type: "GENTLE",
    description: "Soft wake light",
    triggered_at: null,
  },
  status: "SCHEDULED",
  scheduled_at: "2026-01-08T07:00:00Z",
};

const upcomingEvent: Event = {
  id: "event-001",
  user_id: "user-001",
  name: "Call with DataFlow team",
  calendar_id: "calendar-primary",
  platform_id: "zoom-45",
  platform: "Zoom",
  status: "confirmed",
  starts_at: "2026-01-08T14:00:00Z",
  frequency: "ONCE",
  category: "WORK",
  ends_at: "2026-01-08T14:45:00Z",
  created_at: "2026-01-02T12:00:00Z",
  updated_at: "2026-01-05T09:30:00Z",
  people: [
    { id: "person-01", name: "DataFlow team", email: "hello@dataflow.ai" },
  ],
  actions: [],
  date: "2026-01-08",
};

const focusTasks: Task[] = [
  {
    id: "task-001",
    user_id: "user-001",
    scheduled_date: "2026-01-08",
    name: "Recycling goes out tonight",
    status: "READY",
    task_definition: {
      id: "td-001",
      user_id: "user-001",
      name: "Recycling",
      description: "Put bins curbside before 8pm",
      type: "CHORE",
    },
    category: "HOUSE",
    frequency: "ONCE",
    completed_at: null,
    schedule: {
      available_time: null,
      start_time: "2026-01-08T19:00:00Z",
      end_time: "2026-01-08T20:00:00Z",
      timing_type: "TIME_WINDOW",
    },
    routine_id: null,
    tags: ["IMPORTANT"],
    actions: [],
    date: "2026-01-08",
  },
  {
    id: "task-002",
    user_id: "user-001",
    scheduled_date: "2026-01-08",
    name: "Prep morning walk playlist",
    status: "NOT_STARTED",
    task_definition: {
      id: "td-002",
      user_id: "user-001",
      name: "Walk prep",
      description: "Queue three songs that feel light",
      type: "ACTIVITY",
    },
    category: "HEALTH",
    frequency: "ONCE",
    completed_at: null,
    schedule: {
      available_time: null,
      start_time: "2026-01-08T12:30:00Z",
      end_time: "2026-01-08T13:00:00Z",
      timing_type: "TIME_WINDOW",
    },
    routine_id: null,
    tags: ["FUN"],
    actions: [],
    date: "2026-01-08",
  },
  {
    id: "task-003",
    user_id: "user-001",
    scheduled_date: "2026-01-08",
    name: "Refill water bottle",
    status: "COMPLETE",
    task_definition: {
      id: "td-003",
      user_id: "user-001",
      name: "Hydrate",
      description: "Keep the bottle nearby",
      type: "ACTIVITY",
    },
    category: "HEALTH",
    frequency: "DAILY",
    completed_at: "2026-01-08T08:15:00Z",
    schedule: {
      available_time: null,
      start_time: "2026-01-08T08:00:00Z",
      end_time: "2026-01-08T08:30:00Z",
      timing_type: "FIXED_TIME",
    },
    routine_id: "routine-morning",
    tags: ["IMPORTANT"],
    actions: [],
    date: "2026-01-08",
  },
];

const routines: Routine[] = [
  {
    id: "routine-morning",
    user_id: "user-001",
    name: "Morning reset",
    category: "HOUSE",
    routine_schedule: { frequency: "WORK_DAYS", weekdays: [1, 2, 3, 4, 5] },
    description: "Hydrate, open the blinds, step outside for light.",
    tasks: [
      {
        id: "rt-1",
        task_definition_id: "td-003",
        name: "Hydrate",
        schedule: { timing_type: "FLEXIBLE" },
      },
    ],
  },
  {
    id: "routine-evening",
    user_id: "user-001",
    name: "Evening wind-down",
    category: "HEALTH",
    routine_schedule: { frequency: "DAILY" },
    description: "Screens down, stretch, choose tomorrow's focus.",
    tasks: [
      {
        id: "rt-2",
        task_definition_id: "td-004",
        name: "Stretch",
        schedule: { timing_type: "FLEXIBLE" },
      },
    ],
  },
];

const Hero: Component<{
  weekday: string;
  monthDay: string;
  isWorkday: boolean;
}> = (props) => (
  <div class="relative grid md:grid-cols-3 gap-6 items-start">
    <div class="md:col-span-2 space-y-3 pr-28 md:pr-0">
      <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
        {props.weekday}
      </p>
      <h1 class="text-5xl md:text-6xl font-black leading-tight text-stone-900">
        {props.monthDay}
      </h1>
      <p
        class="text-2xl md:text-3xl text-stone-700 italic"
        style={{ "font-family": "'Cormorant Garamond', Georgia, serif" }}
      >
        Good morning, Todd.
      </p>
      <p class="text-stone-600 max-w-xl leading-relaxed">
        A lighter day ahead. You have a client call this afternoon, but the
        morning is yours. Good weather for that walk.
      </p>
    </div>
    <div class="absolute top-0 right-0 flex flex-col items-end gap-2 mt-2">
      <div class="flex items-center gap-2.5 px-3.5 py-2.5 md:px-5 md:py-3 bg-white/70 border border-white/60 rounded-2xl shadow-md shadow-amber-900/5 backdrop-blur">
        <div class="w-8 h-8 md:w-10 md:h-10 rounded-full bg-amber-100/70 flex items-center justify-center">
          <Icon icon={faSun} class="w-4 h-4 md:w-5 md:h-5 fill-amber-500" />
        </div>
        <div class="text-left leading-tight">
          <p class="text-base md:text-lg font-semibold text-stone-800">52°</p>
          <p class="text-[11px] md:text-xs text-stone-500">Sunny</p>
        </div>
      </div>
      <Show when={props.isWorkday}>
        <span class="px-3 py-1.25 md:px-4 md:py-1.5 rounded-full bg-amber-50/95 text-amber-600 text-[11px] md:text-xs font-semibold uppercase tracking-wide border border-amber-100/80 shadow-sm shadow-amber-900/5">
          Workday
        </span>
      </Show>
    </div>
  </div>
);

const ComingUpCard: Component<{ href: string }> = (props) => {
  const timeFormatter = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });

  const formatTimeRange = (startIso: string, endIso?: string | null) => {
    const start = timeFormatter.format(new Date(startIso));
    const end = endIso ? timeFormatter.format(new Date(endIso)) : undefined;
    return end ? `${start} – ${end}` : start;
  };

  return (
    <div class="md:col-span-2 bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <Icon icon={faCalendarDay} class="w-5 h-5 fill-amber-600" />
          <p class="text-xs uppercase tracking-wide text-amber-700">Coming Up</p>
        </div>
        <a
          class="text-xs font-semibold text-amber-700 hover:text-amber-800"
          href={props.href}
        >
          See all events
        </a>
      </div>
      <h3 class="text-xl font-semibold text-stone-800 mb-1">
        {upcomingEvent.name}
      </h3>
      <p class="text-sm text-stone-500">
        {formatTimeRange(upcomingEvent.starts_at, upcomingEvent.ends_at)} ·{" "}
        {upcomingEvent.platform}
      </p>
      <div class="mt-4 flex gap-2 flex-wrap">
        <span class="px-3 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-medium">
          {upcomingEvent.category}
        </span>
        <span class="px-3 py-1 rounded-full bg-stone-50 text-stone-600 text-xs">
          With {upcomingEvent.people?.[0]?.name ?? "team"}
        </span>
      </div>
    </div>
  );
};

const ReminderCard: Component<{ href: string }> = (props) => (
  <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <Icon icon={faBell} class="w-5 h-5 fill-amber-600" />
        <p class="text-xs uppercase tracking-wide text-amber-700">Don't forget</p>
      </div>
      <a
        class="text-xs font-semibold text-amber-700 hover:text-amber-800"
        href={props.href}
      >
        See all tasks
      </a>
    </div>
    <For each={focusTasks.slice(0, 1)}>
      {(task) => (
        <div class="flex items-start gap-3">
          <div class="mt-0.5">
            <Icon icon={faCheckCircle} class="w-4 h-4 fill-amber-600" />
          </div>
          <div class="flex-1">
            <p class="text-sm font-semibold text-stone-800">{task.name}</p>
            <p class="text-xs text-stone-500">
              Before 8pm · {task.task_definition.description}
            </p>
          </div>
        </div>
      )}
    </For>
  </div>
);

const RoutinesCard: Component<{ href: string }> = (props) => (
  <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm md:col-span-2">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <Icon icon={faDroplet} class="w-5 h-5 fill-amber-600" />
        <p class="text-xs uppercase tracking-wide text-amber-700">Routines</p>
      </div>
      <a
        class="text-xs font-semibold text-amber-700 hover:text-amber-800"
        href={props.href}
      >
        See all routines
      </a>
    </div>
    <div class="grid sm:grid-cols-2 gap-4">
      <For each={routines}>
        {(routine) => (
          <div class="rounded-xl bg-amber-50/60 border border-amber-100 p-4">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <Icon
                  icon={routine.id === "routine-morning" ? faSun : faMoon}
                  class="w-4 h-4 fill-amber-700"
                />
                <p class="text-sm font-semibold text-stone-800">
                  {routine.name}
                </p>
              </div>
              <span class="text-[11px] uppercase tracking-wide text-amber-700">
                {routine.routine_schedule.frequency}
              </span>
            </div>
            <p class="text-xs text-stone-600 mb-3">{routine.description}</p>
            <div class="flex gap-2">
              <span class="px-2 py-1 rounded-full bg-white/80 text-xs text-amber-700">
                {routine.category}
              </span>
              <span class="px-2 py-1 rounded-full bg-white/80 text-xs text-stone-600">
                {routine.tasks?.length ?? 0} steps
              </span>
            </div>
          </div>
        )}
      </For>
    </div>
  </div>
);

const FlowCard: Component<{ completionDone: number; completionTotal: number }> = (
  props
) => (
  <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
    <div class="flex items-center gap-3">
      <Icon icon={faPersonRunning} class="w-5 h-5 fill-amber-600" />
      <p class="text-xs uppercase tracking-wide text-amber-700">Today's flow</p>
    </div>
    <div class="flex items-center justify-between">
      <div>
        <p class="text-3xl font-extrabold text-stone-900">
          {props.completionDone}/{props.completionTotal}
        </p>
        <p class="text-xs text-stone-500">Tasks feeling good</p>
      </div>
      <div class="w-14 h-14 rounded-full bg-amber-100/80 flex items-center justify-center">
        <Icon icon={faCheckCircle} class="w-6 h-6 fill-amber-700" />
      </div>
    </div>
    <div class="space-y-3">
      <div class="flex items-center gap-3">
        <Icon icon={faWater} class="w-4 h-4 fill-amber-600" />
        <p class="text-sm text-stone-700">
          Hydration done · {focusTasks[2]?.name}
        </p>
      </div>
      <div class="flex items-center gap-3">
        <Icon icon={faLeaf} class="w-4 h-4 fill-amber-600" />
        <p class="text-sm text-stone-700">
          Morning walk set · playlist queued
        </p>
      </div>
    </div>
  </div>
);

const OverviewPage: Component = () => {
  const date = createMemo(() => new Date(today.date));
  const weekday = createMemo(() =>
    new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(date())
  );
  const monthDay = createMemo(() =>
    new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
    }).format(date())
  );

  const completion = createMemo(() => {
    const done = focusTasks.filter((task) => task.status === "COMPLETE").length;
    return { done, total: focusTasks.length };
  });

  const workdayTag = createMemo(() => today.tags?.includes("WORKDAY"));
  const todayTasksHref = `/me/day/${today.date}`;

  return (
    <Page>
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
            isWorkday={Boolean(workdayTag())}
          />

          <div class="grid md:grid-cols-3 gap-4 md:gap-6">
            <ComingUpCard href="/me/nav/calendar" />
            <ReminderCard href={todayTasksHref} />
          </div>

          <div class="grid md:grid-cols-3 gap-4 md:gap-6">
            <RoutinesCard href="/me/settings/routines" />
            <FlowCard
              completionDone={completion().done}
              completionTotal={completion().total}
            />
          </div>
        </div>
      </div>
    </Page>
  );
};

export default OverviewPage;

