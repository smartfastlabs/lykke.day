import { Component, Show, createMemo, createSignal } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faBullseye } from "@fortawesome/free-solid-svg-icons";
import type { Reminder } from "@/types/api";
import ReminderList from "@/components/reminders/List";
import { useStreamingData } from "@/providers/streamingData";

export interface RemindersSummaryProps {
  reminders: Reminder[];
}

export const RemindersSummary: Component<RemindersSummaryProps> = (props) => {
  const { addReminder, isLoading } = useStreamingData();
  const [newReminderName, setNewReminderName] = createSignal("");
  const [isAdding, setIsAdding] = createSignal(false);

  // Filter out completed and punted reminders - only show active (INCOMPLETE) reminders
  const activeReminders = createMemo(() =>
    props.reminders.filter((r) => r.status === "INCOMPLETE")
  );

  const hasActiveReminders = createMemo(() => activeReminders().length > 0);
  const canAddReminder = createMemo(() => activeReminders().length < 5);

  const handleAddReminder = async () => {
    const name = newReminderName().trim();
    if (!name || isAdding() || !canAddReminder()) return;

    setIsAdding(true);
    try {
      await addReminder(name);
      setNewReminderName("");
    } catch (error) {
      console.error("Failed to add reminder:", error);
    } finally {
      setIsAdding(false);
    }
  };

  const handleKeyPress = (e: globalThis.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAddReminder();
    }
  };

  return (
    <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-6 backdrop-blur-sm">
      <div class="flex items-center gap-3 mb-5">
        <Icon icon={faBullseye} class="w-5 h-5 fill-amber-600" />
        <h3 class="text-lg font-semibold text-stone-800">Reminders</h3>
      </div>

      <Show when={hasActiveReminders()}>
        <div class="space-y-0 mb-4">
          <ReminderList reminders={activeReminders} />
        </div>
      </Show>

      <Show when={canAddReminder()}>
        <div class={hasActiveReminders() ? "pt-2 border-t border-stone-200/50" : ""}>
          <div class="flex gap-2">
            <input
              type="text"
              value={newReminderName()}
              onInput={(e) => setNewReminderName(e.currentTarget.value)}
              onKeyPress={handleKeyPress}
              placeholder="Add a reminder..."
              disabled={isAdding() || isLoading()}
              class="flex-1 px-3 py-2 text-sm bg-white/80 border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed placeholder:text-stone-400"
            />
            <button
              onClick={handleAddReminder}
              disabled={!newReminderName().trim() || isAdding() || isLoading()}
              class="w-9 h-9 flex items-center justify-center bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-amber-500"
              aria-label="Add reminder"
            >
              <Icon key="plus" class="w-4 h-4 fill-white" />
            </button>
          </div>
        </div>
      </Show>
    </div>
  );
};
