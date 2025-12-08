import Page from "../../shared/layout/page";
import { createMemo, For, Component, createResource, Show } from "solid-js";
import { dayAPI } from "../../../utils/api";
import { Day, Task, Event, Alarm } from "../../../types/api";
import type { DayContext, TaskFrequency } from "../../../types/api";

// Frequencies that are "surprising" / infrequent
const INFREQUENT_FREQUENCIES: TaskFrequency[] = [
  "ONCE",
  "YEARLY",
  "MONTHLY",
  "WEEKLY",
];

const isInfrequent = (frequency: TaskFrequency): boolean => {
  return INFREQUENT_FREQUENCIES.includes(frequency);
};

const formatTime = (timeStr: string): string => {
  const date = new Date(timeStr);
  const result = date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });
  console.log("formatTime", timeStr, result);
  return result;
};

const formatAlarmTime = (timeStr: string): string => {
  const [hours, minutes] = timeStr.split(":");
  const h = parseInt(hours);
  const ampm = h >= 12 ? "PM" : "AM";
  const h12 = h % 12 || 12;
  return `${h12}:${minutes} ${ampm}`;
};

// Summary stat component
const StatBlock: Component<{ label: string; count: number }> = (props) => (
  <div class="flex flex-col items-center">
    <span class="text-3xl font-light text-gray-900">{props.count}</span>
    <span class="text-xs uppercase tracking-wide text-gray-400">
      {props.label}
    </span>
  </div>
);

// Infrequent item row
const HighlightRow: Component<{
  name: string;
  subtitle: string;
  time?: string;
  frequency: TaskFrequency;
}> = (props) => (
  <div class="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
    <div class="flex-1 min-w-0">
      <h3 class="text-base font-medium text-gray-900 truncate">{props.name}</h3>
      <div class="flex items-center gap-2">
        <span class="text-xs uppercase tracking-wide text-gray-400">
          {props.subtitle}
        </span>
        <span class="text-xs text-gray-300">•</span>
        <span class="text-xs text-gray-400">
          {props.frequency.toLowerCase().replace("_", " ")}
        </span>
      </div>
    </div>
    <Show when={props.time}>
      <span class="text-sm text-gray-600 border border-gray-200 rounded-full px-3 py-1 ml-3">
        {props.time}
      </span>
    </Show>
  </div>
);

// Alarm row
const AlarmRow: Component<{ alarm: Alarm }> = (props) => (
  <div class="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
    <div class="flex-1 min-w-0">
      <h3 class="text-base font-medium text-gray-900 truncate">
        {props.alarm.name}
      </h3>
      <span class="text-xs uppercase tracking-wide text-gray-400">
        {props.alarm.type}
      </span>
    </div>
    <span class="text-sm text-gray-600 border border-gray-200 rounded-full px-3 py-1 ml-3">
      {formatAlarmTime(props.alarm.time)}
    </span>
  </div>
);

// Section header
const SectionHeader: Component<{ title: string }> = (props) => (
  <h2 class="text-xs uppercase tracking-widest text-gray-400 mb-2">
    {props.title}
  </h2>
);

interface PreviewProps {
  dayContext: DayContext;
}

export const DayPreview: Component<PreviewProps> = (props) => {
  // All items
  const tasks = createMemo(() => props.dayContext?.tasks || []);
  const events = createMemo(() => props.dayContext?.events || []);
  const alarms = createMemo(() => props.dayContext?.day.alarms || []);
  // Filtered to infrequent/surprising items
  const infrequentTasks = createMemo(() =>
    tasks().filter((task) => isInfrequent(task.frequency))
  );
  const infrequentEvents = createMemo(() =>
    events().filter((event) => isInfrequent(event.frequency))
  );
  // Check if there's anything notable to highlight
  const hasHighlights = createMemo(
    () =>
      infrequentTasks().length > 0 ||
      infrequentEvents().length > 0 ||
      alarms().length > 0
  );
  const handleStartDay = () => {
    // TODO: Navigate to main day view or mark day as started
    console.log("Starting day...");
  };
  return (
    <div class="flex flex-col min-h-full px-4 py-6">
      {/* Summary Stats */}
      <div class="flex justify-center gap-8 mb-8 pb-6 border-b border-gray-100">
        <StatBlock label="Tasks" count={tasks().length} />
        <StatBlock label="Events" count={events().length} />
        <StatBlock label="Alarms" count={alarms().length} />
      </div>
      {/* Highlights Section */}
      <div class="flex-1">
        <Show when={alarms().length > 0}>
          <div class="mb-6">
            <SectionHeader title="Alarms" />
            <For each={alarms()}>{(alarm) => <AlarmRow alarm={alarm} />}</For>
          </div>
        </Show>
        {/* Infrequent Events */}
        <Show when={infrequentEvents().length > 0}>
          <div class="mb-6">
            <SectionHeader title="Notable Events" />
            <For each={infrequentEvents()}>
              {(event) => (
                <HighlightRow
                  name={event.name}
                  subtitle="Event"
                  time={formatTime(event.starts_at)}
                  frequency={event.frequency}
                />
              )}
            </For>
          </div>
        </Show>
        {/* Infrequent Tasks */}
        <Show when={infrequentTasks().length > 0}>
          <div class="mb-6">
            <SectionHeader title="Don't Forget" />
            <For each={infrequentTasks()}>
              {(task) => (
                <HighlightRow
                  name={task.name}
                  subtitle={task.task_definition.type}
                  time={
                    task.schedule?.time
                      ? formatAlarmTime(task.schedule.time)
                      : undefined
                  }
                  frequency={task.frequency}
                />
              )}
            </For>
          </div>
        </Show>
      </div>
    </div>
  );
};

export default DayPreview;
