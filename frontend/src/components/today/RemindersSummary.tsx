import { Component, Show, createMemo } from "solid-js";
import { useNavigate } from "@solidjs/router";
import { Icon } from "@/components/shared/Icon";
import { faBullseye, faPlus } from "@fortawesome/free-solid-svg-icons";
import type { Reminder } from "@/types/api";
import ReminderList from "@/components/reminders/List";

export interface RemindersSummaryProps {
  reminders: Reminder[];
  href?: string;
}

export const RemindersSummary: Component<RemindersSummaryProps> = (props) => {
  const navigate = useNavigate();

  // Filter out completed and punted reminders - only show active (INCOMPLETE) reminders
  const activeReminders = createMemo(() =>
    props.reminders.filter((r) => r.status === "INCOMPLETE")
  );

  const otherCount = createMemo(
    () => props.reminders.filter((r) => r.status !== "INCOMPLETE").length
  );
  const hasLink = createMemo(() => Boolean(props.href));

  return (
    <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
      <div class="flex items-center justify-between">
        <Show
          when={hasLink()}
          fallback={
            <div class="flex items-center gap-3 text-left">
              <Icon icon={faBullseye} class="w-5 h-5 fill-amber-600" />
              <p class="text-xs uppercase tracking-wide text-amber-700">Reminders</p>
            </div>
          }
        >
          <button
            type="button"
            onClick={() => navigate(props.href!)}
            class="flex items-center gap-3 text-left"
            aria-label="See all reminders"
          >
            <Icon icon={faBullseye} class="w-5 h-5 fill-amber-600" />
            <p class="text-xs uppercase tracking-wide text-amber-700">Reminders</p>
          </button>
        </Show>
        <div class="flex items-center gap-3">
          <button
            onClick={() => navigate("/me/add-reminder")}
            class="w-6 h-6 flex items-center justify-center rounded-full bg-amber-600 text-white hover:bg-amber-700 transition-colors"
            aria-label="Add reminder"
          >
            <Icon icon={faPlus} class="w-3 h-3" />
          </button>
        </div>
      </div>
      <Show when={activeReminders().length > 0}>
        <div class="space-y-1">
          <ReminderList reminders={activeReminders} />
        </div>
      </Show>
      <Show when={otherCount() > 0}>
        <p class="text-xs text-stone-500">
          {otherCount()} other reminder{otherCount() !== 1 ? "s" : ""}
        </p>
      </Show>
      <Show when={activeReminders().length === 0 && otherCount() === 0}>
        <p class="text-xs text-stone-500">No reminders</p>
      </Show>
    </div>
  );
};
