import { Component, For, Show } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faBell, faCheckCircle } from "@fortawesome/free-solid-svg-icons";
import type { Task } from "@/types/api";

export interface ReminderCardProps {
  tasks: Task[];
  href: string;
}

export const ReminderCard: Component<ReminderCardProps> = (props) => (
  <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <Icon icon={faBell} class="w-5 h-5 fill-amber-600" />
        <p class="text-xs uppercase tracking-wide text-amber-700">Don't forget</p>
      </div>
      <a
        class="text-xs font-semibold text-amber-700 hover:text-amber-800"
        href={props.href}
      >
        See all tasks
      </a>
    </div>
    <Show when={props.tasks.length > 0}>
      <For each={props.tasks.slice(0, 1)}>
        {(task) => (
          <div class="flex items-start gap-3">
            <div class="mt-0.5">
              <Icon icon={faCheckCircle} class="w-4 h-4 fill-amber-600" />
            </div>
            <div class="flex-1">
              <p class="text-sm font-semibold text-stone-800">{task.name}</p>
              <p class="text-xs text-stone-500">
                Before 8pm · {task.task_definition.description}
              </p>
            </div>
          </div>
        )}
      </For>
    </Show>
  </div>
);

