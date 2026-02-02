import { Component, Show, createMemo, createResource } from "solid-js";
import { useParams } from "@solidjs/router";
import Page from "@/components/shared/layout/Page";
import {
  TasksSection,
  EventsSection,
  RoutineSummary,
  RemindersSummary,
} from "@/components/today";
import { notificationAPI } from "@/utils/api";
import { filterVisibleTasks } from "@/utils/tasks";

export const PushNotificationDetailPage: Component = () => {
  const params = useParams();
  const [context] = createResource(
    () => params.id,
    (id) => notificationAPI.getContext(id),
  );

  const tasks = createMemo(() => context()?.tasks ?? []);
  const reminders = createMemo(() =>
    tasks().filter((task) => task.type === "REMINDER"),
  );
  const routines = createMemo(() => context()?.routines ?? []);
  const events = createMemo(() => context()?.calendar_entries ?? []);

  const visibleTasks = createMemo(() => filterVisibleTasks(tasks()));

  const headline = createMemo(() => {
    const notification = context()?.notification;
    if (notification?.message) return notification.message;
    if (!notification?.content) return "Push notification";
    try {
      const parsed = JSON.parse(notification.content) as { body?: string };
      return parsed.body ?? "Push notification";
    } catch {
      return "Push notification";
    }
  });

  return (
    <Page variant="app" hideFooter>
      <div class="min-h-[100dvh] box-border relative overflow-hidden">
        <div class="relative z-10 max-w-4xl mx-auto px-6 py-6">
          <div class="mb-6 space-y-2">
            <h1 class="text-xl font-semibold text-stone-800">{headline()}</h1>
            <p class="text-sm text-stone-500">
              Complete or punt the items tied to this notification.
            </p>
          </div>

          <Show
            when={!context.loading}
            fallback={<div class="text-stone-400">Loading...</div>}
          >
            <Show
              when={
                visibleTasks().length > 0 ||
                reminders().length > 0 ||
                routines().length > 0 ||
                events().length > 0
              }
              fallback={
                <div class="text-stone-400">
                  No referenced items for this notification.
                </div>
              }
            >
              <Show when={reminders().length > 0}>
                <div class="mb-6">
                  <RemindersSummary reminders={reminders()} />
                </div>
              </Show>
              <Show when={visibleTasks().length > 0}>
                <div class="mb-6">
                  <TasksSection tasks={visibleTasks()} href="/me/today/tasks" />
                </div>
              </Show>
              <Show when={events().length > 0}>
                <div class="mb-6">
                  <EventsSection events={events()} href="/me/today/events" />
                </div>
              </Show>
              <Show when={routines().length > 0}>
                <div class="mb-6">
                  <RoutineSummary tasks={tasks()} routines={routines()} />
                </div>
              </Show>
            </Show>
          </Show>
        </div>
      </div>
    </Page>
  );
};

export default PushNotificationDetailPage;
