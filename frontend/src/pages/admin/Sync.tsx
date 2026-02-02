import { Component, For, Show, createMemo, createSignal } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import { useStreamingData } from "@/providers/streamingData";
import ReadOnlyTaskList from "@/components/tasks/ReadOnlyList";
import ReadOnlyReminderList from "@/components/reminders/ReadOnlyList";
import ReadOnlyAlarmList from "@/components/alarms/ReadOnlyList";
import ReadOnlyRoutineGroupsChronologicalList from "@/components/routines/ReadOnlyRoutineGroupsChronologicalList";
import EventList from "@/components/events/List";
import SettingsList from "@/components/shared/SettingsList";
import TodayBrainDumpListItem from "@/components/brain-dump/TodayBrainDumpListItem";
import TodayNotificationListItem from "@/components/notifications/TodayNotificationListItem";
import type {
  Alarm,
  BrainDump,
  Event,
  PushNotification,
  Routine,
  Task,
} from "@/types/api";

const formatTimestamp = (isoString: string): string => {
  const date = new Date(isoString);
  return date.toLocaleString();
};

const StreamingSyncPage: Component = () => {
  const {
    isConnected,
    isLoading,
    isOutOfSync,
    error,
    dayContext,
    tasks,
    events,
    reminders,
    alarms,
    brainDumps,
    notifications,
    routines,
    sync,
    lastProcessedTimestamp,
    lastChangeStreamId,
    debugEvents,
    clearDebugEvents,
  } = useStreamingData();

  const [expandedLogEntries, setExpandedLogEntries] = createSignal<Set<string>>(
    new Set(),
  );
  const [selectedItem, setSelectedItem] = createSignal<{
    label: string;
    payload: unknown;
  } | null>(null);

  const toggleExpanded = (id: string) => {
    setExpandedLogEntries((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const logEntries = createMemo(() => debugEvents());
  const routineList = createMemo<Routine[]>(() => routines() ?? []);

  const selectItem = (label: string, payload: unknown) => {
    setSelectedItem({ label, payload });
  };

  const selectTask = (task: Task) => selectItem("Task", task);
  const selectReminder = (reminder: Task) => selectItem("Reminder", reminder);
  const selectAlarm = (alarm: Alarm) => selectItem("Alarm", alarm);
  const selectEvent = (event: Event) => selectItem("Event", event);
  const selectBrainDump = (item: BrainDump) =>
    selectItem("Brain dump", item);
  const selectNotification = (item: PushNotification) =>
    selectItem("Notification", item);
  const selectRoutineByDefinitionId = (routineDefinitionId: string) => {
    const routine = routineList().find(
      (item) => item.routine_definition_id === routineDefinitionId,
    );
    if (routine) {
      selectItem("Routine", routine);
      return;
    }
    selectItem("Routine", { routine_definition_id: routineDefinitionId });
  };

  return (
    <SettingsPage heading="Streaming Sync">
      <div class="space-y-6">
        <section class="rounded-3xl border border-amber-100/80 bg-white/80 p-6 shadow-sm shadow-amber-900/5">
          <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div class="space-y-1">
              <h2 class="text-lg font-semibold text-stone-800">Status</h2>
              <p class="text-sm text-stone-500">
                Live connection state and key sync markers.
              </p>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => sync()}
                class="inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-100/70 px-4 py-2 text-sm font-semibold text-amber-800 hover:bg-amber-100"
              >
                Request full sync
              </button>
              <button
                type="button"
                onClick={() => clearDebugEvents()}
                class="inline-flex items-center gap-2 rounded-full border border-stone-200 bg-white/80 px-4 py-2 text-sm font-semibold text-stone-600 hover:bg-stone-50"
              >
                Clear log
              </button>
            </div>
          </div>

          <div class="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <div class="rounded-2xl border border-amber-100/70 bg-amber-50/40 p-4">
              <div class="text-xs uppercase tracking-wide text-stone-400">
                Connection
              </div>
              <div class="mt-2 flex items-center gap-2 text-sm text-stone-700">
                <span
                  class={`h-2 w-2 rounded-full ${
                    isConnected() ? "bg-emerald-500" : "bg-rose-500"
                  }`}
                />
                {isConnected() ? "Connected" : "Disconnected"}
              </div>
              <div class="mt-2 text-xs text-stone-500">
                Loading: {isLoading() ? "Yes" : "No"}
              </div>
              <div class="mt-1 text-xs text-stone-500">
                Out of sync: {isOutOfSync() ? "Yes" : "No"}
              </div>
            </div>

            <div class="rounded-2xl border border-amber-100/70 bg-white/70 p-4">
              <div class="text-xs uppercase tracking-wide text-stone-400">
                Last markers
              </div>
              <div class="mt-2 text-xs text-stone-600">
                Last audit log:
                <span class="ml-2 font-mono text-stone-700">
                  {lastProcessedTimestamp() ?? "—"}
                </span>
              </div>
              <div class="mt-2 text-xs text-stone-600">
                Change stream:
                <span class="ml-2 font-mono text-stone-700">
                  {lastChangeStreamId() ?? "—"}
                </span>
              </div>
              <Show when={error()}>
                <div class="mt-2 text-xs text-rose-600">
                  Error: {error()?.message}
                </div>
              </Show>
            </div>

            <div class="rounded-2xl border border-amber-100/70 bg-white/70 p-4">
              <div class="text-xs uppercase tracking-wide text-stone-400">
                Totals
              </div>
              <div class="mt-2 grid grid-cols-2 gap-2 text-xs text-stone-600">
                <div>Tasks: {tasks().length}</div>
                <div>Events: {events().length}</div>
                <div>Reminders: {reminders().length}</div>
                <div>Alarms: {alarms().length}</div>
                <div>Brain dumps: {brainDumps().length}</div>
                <div>Notifications: {notifications().length}</div>
                <div>Routines: {routines().length}</div>
                <div>Day context: {dayContext() ? "Loaded" : "Empty"}</div>
              </div>
            </div>
          </div>

          <div class="mt-4">
            <button
              type="button"
              onClick={() => selectItem("Day context", dayContext())}
              class="text-xs font-semibold text-amber-700 hover:text-amber-800"
            >
              View day context JSON
            </button>
          </div>
        </section>

        <section class="rounded-3xl border border-amber-100/80 bg-white/80 p-6 shadow-sm shadow-amber-900/5">
          <div class="flex items-center justify-between gap-4">
            <div class="space-y-1">
              <h2 class="text-lg font-semibold text-stone-800">
                Day context view
              </h2>
              <p class="text-sm text-stone-500">
                Browse the current state. Click any item to inspect JSON.
              </p>
            </div>
          </div>

          <div class="mt-6 grid gap-6 lg:grid-cols-2">
            <div class="space-y-4">
              <div class="rounded-2xl border border-amber-100/70 bg-white/70 p-4">
                <div class="text-xs uppercase tracking-wide text-stone-400 mb-3">
                  Tasks
                </div>
                <Show
                  when={tasks().length > 0}
                  fallback={
                    <div class="text-sm text-stone-500">No tasks loaded.</div>
                  }
                >
                  <ReadOnlyTaskList tasks={tasks} onItemClick={selectTask} />
                </Show>
              </div>

              <div class="rounded-2xl border border-amber-100/70 bg-white/70 p-4">
                <div class="text-xs uppercase tracking-wide text-stone-400 mb-3">
                  Reminders
                </div>
                <Show
                  when={reminders().length > 0}
                  fallback={
                    <div class="text-sm text-stone-500">
                      No reminders loaded.
                    </div>
                  }
                >
                  <ReadOnlyReminderList
                    reminders={reminders}
                    onItemClick={selectReminder}
                  />
                </Show>
              </div>

              <div class="rounded-2xl border border-amber-100/70 bg-white/70 p-4">
                <div class="text-xs uppercase tracking-wide text-stone-400 mb-3">
                  Alarms
                </div>
                <Show
                  when={alarms().length > 0}
                  fallback={
                    <div class="text-sm text-stone-500">
                      No alarms loaded.
                    </div>
                  }
                >
                  <ReadOnlyAlarmList
                    alarms={alarms}
                    onItemClick={selectAlarm}
                  />
                </Show>
              </div>

              <div class="rounded-2xl border border-amber-100/70 bg-white/70 p-4">
                <div class="text-xs uppercase tracking-wide text-stone-400 mb-3">
                  Events
                </div>
                <Show
                  when={events().length > 0}
                  fallback={
                    <div class="text-sm text-stone-500">
                      No events loaded.
                    </div>
                  }
                >
                  <div class="overflow-hidden rounded-xl border border-stone-100">
                    <EventList events={events} onItemClick={selectEvent} />
                  </div>
                </Show>
              </div>
            </div>

            <div class="space-y-4">
              <div class="rounded-2xl border border-amber-100/70 bg-white/70 p-4">
                <div class="text-xs uppercase tracking-wide text-stone-400 mb-3">
                  Routines
                </div>
                <Show
                  when={routineList().length > 0}
                  fallback={
                    <div class="text-sm text-stone-500">
                      No routines loaded.
                    </div>
                  }
                >
                  <ReadOnlyRoutineGroupsChronologicalList
                    tasks={tasks()}
                    routines={routineList()}
                    expandedByDefault={true}
                    onTaskClick={selectTask}
                    onRoutineClick={selectRoutineByDefinitionId}
                  />
                </Show>
              </div>

              <div class="rounded-2xl border border-amber-100/70 bg-white/70 p-4">
                <div class="text-xs uppercase tracking-wide text-stone-400 mb-3">
                  Brain dumps
                </div>
                <SettingsList
                  items={brainDumps()}
                  getItemLabel={(item) => item.text ?? "Brain dump"}
                  renderItem={(item) => <TodayBrainDumpListItem item={item} />}
                  onItemClick={selectBrainDump}
                  emptyStateLabel="No brain dumps."
                  searchPlaceholder="Search brain dumps..."
                />
              </div>

              <div class="rounded-2xl border border-amber-100/70 bg-white/70 p-4">
                <div class="text-xs uppercase tracking-wide text-stone-400 mb-3">
                  Notifications
                </div>
                <SettingsList
                  items={notifications()}
                  getItemLabel={(item) => item.message ?? "Notification"}
                  renderItem={(item) => (
                    <TodayNotificationListItem notification={item} />
                  )}
                  onItemClick={selectNotification}
                  emptyStateLabel="No notifications."
                  searchPlaceholder="Search notifications..."
                />
              </div>
            </div>
          </div>

          <div class="mt-6 rounded-2xl border border-stone-200 bg-stone-50/80 p-4">
            <div class="text-xs uppercase tracking-wide text-stone-400">
              Selected JSON
            </div>
            <Show
              when={selectedItem()}
              fallback={
                <div class="mt-2 text-sm text-stone-500">
                  Click any item to inspect its JSON payload.
                </div>
              }
            >
              <div class="mt-3 text-xs font-semibold text-stone-700">
                {selectedItem()?.label}
              </div>
              <pre class="mt-2 max-h-80 overflow-auto rounded-xl bg-stone-900/90 p-4 text-xs text-amber-100">
                {JSON.stringify(selectedItem()?.payload ?? null, null, 2)}
              </pre>
            </Show>
          </div>
        </section>

        <section class="rounded-3xl border border-amber-100/80 bg-white/80 p-6 shadow-sm shadow-amber-900/5">
          <div class="flex items-center justify-between">
            <div class="space-y-1">
              <h2 class="text-lg font-semibold text-stone-800">Event log</h2>
              <p class="text-sm text-stone-500">
                Most recent entries first ({logEntries().length}).
              </p>
            </div>
          </div>

          <div class="mt-5 space-y-2">
            <Show
              when={logEntries().length > 0}
              fallback={
                <div class="rounded-2xl border border-dashed border-stone-200 bg-stone-50/80 p-6 text-center text-sm text-stone-500">
                  No log entries yet.
                </div>
              }
            >
              <For each={logEntries()}>
                {(entry) => (
                  <div
                    class="rounded-2xl border border-stone-100 bg-white p-4 shadow-sm transition hover:border-stone-200"
                    onClick={() => toggleExpanded(entry.id)}
                  >
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <div class="flex items-center gap-3">
                        <span
                          class={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                            entry.direction === "in"
                              ? "bg-emerald-100 text-emerald-700"
                              : entry.direction === "out"
                                ? "bg-sky-100 text-sky-700"
                                : entry.direction === "error"
                                  ? "bg-rose-100 text-rose-700"
                                  : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {entry.direction.toUpperCase()}
                        </span>
                        <span class="text-sm font-mono text-stone-700">
                          {entry.label}
                        </span>
                      </div>
                      <span class="text-xs text-stone-400">
                        {formatTimestamp(entry.timestamp)}
                      </span>
                    </div>
                    <Show when={expandedLogEntries().has(entry.id)}>
                      <div class="mt-3 border-t border-stone-100 pt-3">
                        <div class="text-xs uppercase tracking-wide text-stone-400">
                          Payload
                        </div>
                        <pre class="mt-2 max-h-64 overflow-auto rounded-xl bg-stone-100/70 p-3 text-xs text-stone-600">
                          {JSON.stringify(entry.payload ?? null, null, 2)}
                        </pre>
                      </div>
                    </Show>
                  </div>
                )}
              </For>
            </Show>
          </div>
        </section>
      </div>
    </SettingsPage>
  );
};

export default StreamingSyncPage;
