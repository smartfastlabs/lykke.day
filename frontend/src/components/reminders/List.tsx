import { Component, For, Show } from "solid-js";
import type { Accessor } from "solid-js";
import type { Task, TaskStatus } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streamingData";
import { SwipeableItem } from "@/components/shared/SwipeableItem";

const getStatusClasses = (status: TaskStatus): string => {
  switch (status) {
    case "COMPLETE":
      return "bg-stone-50/50";
    case "PUNT":
      return "bg-amber-50/30 italic";
    default:
      return "";
  }
};

const ReminderItem: Component<{ reminder: Task }> = (props) => {
  const { updateReminderStatus, removeReminder } = useStreamingData();

  const handleSwipeLeft = () => {
    if (props.reminder.status === "COMPLETE") {
      removeReminder(props.reminder.id);
    } else {
      updateReminderStatus(props.reminder, "PUNT");
    }
  };

  return (
    <SwipeableItem
      onSwipeRight={() => updateReminderStatus(props.reminder, "COMPLETE")}
      onSwipeLeft={handleSwipeLeft}
      rightLabel="✅ Complete Reminder"
      leftLabel={props.reminder.status === "COMPLETE" ? "🗑 Remove" : "⏸ Punt"}
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
          <div class="flex-shrink-0 w-4 text-amber-600">
            <Icon key="checkMark" />
          </div>
        </Show>
      </div>
    </SwipeableItem>
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
