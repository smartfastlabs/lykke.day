import {
  Component,
  Show,
  createMemo,
  createSignal,
  onCleanup,
  onMount,
} from "solid-js";
import { Icon } from "@/components/shared/Icon";
import {
  faCheckCircle,
  faChevronDown,
} from "@fortawesome/free-solid-svg-icons";
import type { Task } from "@/types/api";
import {
  getTaskAvailableTime,
  getTaskDueByTime,
  isTaskAvailable,
} from "@/utils/tasks";
import TaskList from "@/components/tasks/List";

export interface AvailableSectionProps {
  tasks: Task[];
}

export const AvailableSection: Component<AvailableSectionProps> = (props) => {
  const [now, setNow] = createSignal(new Date());
  const [expanded, setExpanded] = createSignal(false);

  // Update time every 30 seconds to keep the section reactive
  onMount(() => {
    const interval = setInterval(() => {
      setNow(new Date());
    }, 30000);

    onCleanup(() => {
      clearInterval(interval);
    });
  });

  const availableTasks = createMemo(() => {
    const currentTime = now();
    return props.tasks
      .filter((task) => isTaskAvailable(task, currentTime))
      .sort((a, b) => {
        const aDue = getTaskDueByTime(a);
        const bDue = getTaskDueByTime(b);
        if (aDue && bDue) {
          return aDue.getTime() - bDue.getTime();
        }
        const aAvailable = getTaskAvailableTime(a);
        const bAvailable = getTaskAvailableTime(b);
        if (!aAvailable || !bAvailable) return 0;
        return aAvailable.getTime() - bAvailable.getTime();
      });
  });

  return (
    <Show when={availableTasks().length > 0}>
      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-3 backdrop-blur-sm space-y-2">
        <button
          type="button"
          class="w-full flex items-center justify-between text-left"
          onClick={() => setExpanded(!expanded())}
          aria-expanded={expanded()}
        >
          <div class="flex items-center gap-2">
            <Icon icon={faCheckCircle} class="w-3 h-3 fill-amber-600" />
            <p class="text-[10px] uppercase tracking-wide text-amber-700">
              Available
            </p>
          </div>
          <div class="flex items-center gap-2">
            <Show when={!expanded()}>
              <span class="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700">
                {availableTasks().length}
              </span>
            </Show>
            <Icon
              icon={faChevronDown}
              class={`w-3 h-3 text-amber-600 transition-transform ${
                expanded() ? "rotate-180" : ""
              }`}
            />
          </div>
        </button>

        <Show when={expanded()}>
          <div class="space-y-1">
            <p class="text-[11px] font-medium text-stone-500">Tasks</p>
            <div class="space-y-1">
              <TaskList tasks={() => availableTasks()} />
            </div>
          </div>
        </Show>
      </div>
    </Show>
  );
};
