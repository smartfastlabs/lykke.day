import { Component, For, Show, createSignal } from "solid-js";
import type { Accessor } from "solid-js";
import type { Task, TaskStatus } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streamingData";
import { SwipeableItem } from "@/components/shared/SwipeableItem";
import ReminderActionModal from "@/components/shared/ReminderActionModal";

const getStatusClasses = (status: TaskStatus): string => {
  switch (status) {
    case "COMPLETE":
      return "bg-stone-50/50";
    case "PUNT":
      return "bg-amber-50/30 italic";
    case "SNOOZE":
      return "bg-sky-50/50";
    default:
      return "";
  }
};

const ReminderItem: Component<{ reminder: Task }> = (props) => {
  const { updateReminderStatus, removeReminder, rescheduleTask } =
    useStreamingData();
  const [pendingReminder, setPendingReminder] = createSignal<Task | null>(null);
  const getTomorrowDateString = (): string => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toLocaleDateString("en-CA");
  };

  const handleSwipeLeft = () => {
    if (props.reminder.status === "COMPLETE") {
      const reminderId = props.reminder.id;
      if (!reminderId) return;
      removeReminder(reminderId);
    } else {
      setPendingReminder(props.reminder);
    }
  };

  return (
    <>
      <SwipeableItem
        onSwipeRight={() => updateReminderStatus(props.reminder, "COMPLETE")}
        onSwipeLeft={handleSwipeLeft}
        rightLabel="✅ Complete Reminder"
        leftLabel={
          props.reminder.status === "COMPLETE"
            ? "🗑 Remove"
            : "⏸ Punt or Tomorrow"
        }
        statusClass={getStatusClasses(props.reminder.status)}
        compact={true}
      >
        <div class="flex items-center gap-4">
          <span class="w-4 flex-shrink-0 flex items-center justify-center text-amber-600">
            <span class="text-lg">🎯</span>
          </span>
          <div class="flex-1 min-w-0">
            <span
              class={`text-sm truncate block ${
                props.reminder.status === "COMPLETE"
                  ? "line-through text-stone-400"
                  : "text-stone-800"
              }`}
            >
              {props.reminder.name}
            </span>
          </div>
          <Show when={props.reminder.status === "COMPLETE"}>
            <div class="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center">
              <Icon key="checkMark" class="w-3 h-3 fill-current" />
            </div>
          </Show>
        </div>
      </SwipeableItem>
      <ReminderActionModal
        isOpen={Boolean(pendingReminder())}
        title="Punt or Remind me Tomorrow"
        onClose={() => setPendingReminder(null)}
        onPunt={() => {
          const reminder = pendingReminder();
          if (!reminder) return;
          setPendingReminder(null);
          void updateReminderStatus(reminder, "PUNT");
        }}
        onRemindTomorrow={() => {
          const reminder = pendingReminder();
          if (!reminder) return;
          setPendingReminder(null);
          const tomorrowDate = getTomorrowDateString();
          void rescheduleTask(reminder, tomorrowDate);
        }}
      />
    </>
  );
};

interface ReminderListProps {
  reminders: Accessor<Task[]>;
}

const ReminderList: Component<ReminderListProps> = (props) => {
  const reminders = () => props.reminders() ?? [];

  return (
    <>
      <For each={reminders()}>
        {(reminder) => <ReminderItem reminder={reminder} />}
      </For>
    </>
  );
};

export default ReminderList;
