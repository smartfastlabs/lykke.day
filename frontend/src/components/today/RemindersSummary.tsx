import { Component, Show, createMemo } from "solid-js";
import { useNavigate } from "@solidjs/router";
import { Icon } from "@/components/shared/Icon";
import { faBullseye, faPlus } from "@fortawesome/free-solid-svg-icons";
import type { Task } from "@/types/api";
import ReminderList from "@/components/reminders/List";
import { FuzzyCard, FuzzyLine } from "./FuzzyCard";

export interface RemindersSummaryProps {
  reminders: Task[];
  href?: string;
  isLoading?: boolean;
}

export const RemindersSummary: Component<RemindersSummaryProps> = (props) => {
  const navigate = useNavigate();

  // Filter to active reminder tasks (not COMPLETE or PUNT)
  const activeReminders = createMemo(() =>
    props.reminders.filter(
      (r) => r.status !== "COMPLETE" && r.status !== "PUNT",
    ),
  );

  const hasLink = createMemo(() => Boolean(props.href));

  return (
    <Show
      when={!props.isLoading || props.reminders.length > 0}
      fallback={
        <FuzzyCard class="p-5 space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="h-4 w-4 rounded-full bg-amber-200/90" />
              <FuzzyLine class="h-2 w-20" />
            </div>
            <div class="h-9 w-9 rounded-full bg-amber-100/90" />
          </div>
          <div class="space-y-2">
            <FuzzyLine class="h-3 w-full" />
            <FuzzyLine class="h-3 w-4/5" />
            <FuzzyLine class="h-3 w-3/5" />
          </div>
        </FuzzyCard>
      }
    >
      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
        <div class="flex items-center justify-between">
          <Show
            when={hasLink()}
            fallback={
              <div class="flex items-center gap-3 text-left">
                <Icon icon={faBullseye} class="w-5 h-5 fill-amber-600" />
                <p class="text-xs uppercase tracking-wide text-amber-700">
                  Reminders
                </p>
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
              <p class="text-xs uppercase tracking-wide text-amber-700">
                Reminders
              </p>
            </button>
          </Show>
          <div class="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate("/me/add-reminder")}
              class="inline-flex items-center justify-center w-9 h-9 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-600/80 transition hover:bg-amber-100/80 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Add reminder"
              title="Add reminder"
            >
              <Icon icon={faPlus} class="w-4 h-4 fill-amber-600/80" />
            </button>
          </div>
        </div>
        <Show when={activeReminders().length > 0}>
          <div class="space-y-1">
            <ReminderList reminders={activeReminders} />
          </div>
        </Show>
      </div>
    </Show>
  );
};
