import { Component, createMemo } from "solid-js";
import { faWater, faLeaf } from "@fortawesome/free-solid-svg-icons";
import { DayOverview } from "@/components/overview";
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
    <DayOverview
      withPageWrapper
      hero={{
        weekday: weekday(),
        monthDay: monthDay(),
        isWorkday: Boolean(workdayTag()),
        userName: "Todd",
        description:
          "A lighter day ahead. You have a client call this afternoon, but the morning is yours. Good weather for that walk.",
      }}
      comingUp={{
        event: upcomingEvent,
        href: "/me/nav/calendar",
      }}
      reminder={{
        tasks: focusTasks,
        href: todayTasksHref,
      }}
      routines={{
        routines,
        href: "/me/settings/routines",
      }}
      flow={{
        completionDone: completion().done,
        completionTotal: completion().total,
        items: [
          {
            icon: faWater,
            text: `Hydration done · ${focusTasks[2]?.name}`,
          },
          {
            icon: faLeaf,
            text: "Morning walk set · playlist queued",
          },
        ],
      }}
    />
  );
};

export default OverviewPage;
