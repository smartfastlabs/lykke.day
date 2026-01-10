import Page from "@/components/shared/layout/Page";
import { Show, Component, createMemo, ParentProps } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import { DayOverview } from "@/components/overview";
import { faWater, faLeaf } from "@fortawesome/free-solid-svg-icons";

export const HomeLayout: Component<ParentProps> = (props) => {
  const { dayContext, tasks, events, day, isLoading } = useSheppard();

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

  const upcomingEvent = createMemo(() => {
    const allEvents = events();
    if (!allEvents || allEvents.length === 0) return undefined;

    // Find the next upcoming event
    const now = new Date();
    const upcoming = allEvents
      .filter((e) => new Date(e.starts_at) > now)
      .sort(
        (a, b) =>
          new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime()
      );

    return upcoming[0];
  });

  const importantTasks = createMemo(() => {
    const allTasks = tasks();
    if (!allTasks || allTasks.length === 0) return [];

    // Filter for important/pending tasks
    return allTasks
      .filter(
        (t) =>
          t.status !== "COMPLETE" &&
          (t.tags?.includes("IMPORTANT") || t.category === "HOUSE")
      )
      .slice(0, 3);
  });

  const completion = createMemo(() => {
    const allTasks = tasks();
    if (!allTasks || allTasks.length === 0) return { done: 0, total: 0 };

    const done = allTasks.filter((task) => task.status === "COMPLETE").length;
    return { done, total: allTasks.length };
  });

  const completedTasks = createMemo(() => {
    const allTasks = tasks();
    if (!allTasks || allTasks.length === 0) return [];

    return allTasks.filter((task) => task.status === "COMPLETE").slice(0, 2);
  });

  const flowItems = createMemo(() => {
    const completed = completedTasks();
    return completed.map((task, index) => ({
      icon: index === 0 ? faWater : faLeaf,
      text: `${task.name} completed`,
    }));
  });

  return (
    <Page>
      <Show
        when={!isLoading() && dayContext()}
        fallback={<div class="p-8 text-center text-gray-400">Loading...</div>}
      >
        <DayOverview
          withPageWrapper={false}
          hero={{
            weekday: weekday(),
            monthDay: monthDay(),
            isWorkday: isWorkday(),
            description: `You have ${events().length} events and ${tasks().length} tasks scheduled for today.`,
          }}
          comingUp={
            upcomingEvent()
              ? {
                  event: upcomingEvent()!,
                  href: "/me/nav/calendar",
                }
              : undefined
          }
          reminder={
            importantTasks().length > 0
              ? {
                  tasks: importantTasks(),
                  href: `/me/day/${day()?.date || ""}`,
                }
              : undefined
          }
          flow={
            completion().total > 0
              ? {
                  completionDone: completion().done,
                  completionTotal: completion().total,
                  items: flowItems(),
                }
              : undefined
          }
        />
        {props.children}
      </Show>
    </Page>
  );
};

export default HomeLayout;
