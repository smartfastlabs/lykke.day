import { Component, For } from "solid-js";
import type { Accessor } from "solid-js";
import type { Task } from "@/types/api";

export interface ReadOnlyReminderListProps {
  reminders: Accessor<Task[]>;
}

export const ReadOnlyReminderList: Component<ReadOnlyReminderListProps> = (
  props,
) => {
  const items = () => props.reminders() ?? [];

  return (
    <div class="space-y-2">
      <For each={items()}>
        {(reminder) => (
          <div class="bg-white/70 border border-white/70 shadow shadow-amber-900/5 rounded-2xl px-4 py-3 backdrop-blur-sm">
            <div class="flex items-center gap-3">
              <span class="w-4 flex-shrink-0 flex items-center justify-center text-amber-600">
                <span class="text-lg">🎯</span>
              </span>
              <div class="flex-1 min-w-0">
                <span class="text-sm text-stone-800 truncate block">
                  {reminder.name}
                </span>
              </div>
              <span class="text-[10px] uppercase tracking-wide text-stone-500">
                {reminder.status === "NOT_STARTED" ||
                reminder.status === "READY" ||
                reminder.status === "PENDING"
                  ? "active"
                  : reminder.status.toLowerCase()}
              </span>
            </div>
          </div>
        )}
      </For>
    </div>
  );
};

export default ReadOnlyReminderList;
