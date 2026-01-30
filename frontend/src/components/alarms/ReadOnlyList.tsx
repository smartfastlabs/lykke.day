import { Component, For, Show } from "solid-js";
import type { Accessor } from "solid-js";
import type { Alarm } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import {
  faArrowUpRightFromSquare,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";

const formatTime = (timeValue: string): string => {
  const trimmed = timeValue.trim();
  const [rawHours, rawMinutes] = trimmed.split(":");
  const hours = Number.parseInt(rawHours ?? "", 10);
  const minutes = Number.parseInt(rawMinutes ?? "", 10);
  if (Number.isNaN(hours) || Number.isNaN(minutes)) return trimmed;
  const period = hours >= 12 ? "pm" : "am";
  const hour12 = hours % 12 || 12;
  return `${hour12}:${String(minutes).padStart(2, "0")}${period}`;
};

export interface ReadOnlyAlarmListProps {
  alarms: Accessor<Alarm[]>;
  onRemove?: (alarm: Alarm) => void | Promise<void>;
}

export const ReadOnlyAlarmList: Component<ReadOnlyAlarmListProps> = (props) => {
  const items = () => props.alarms() ?? [];

  return (
    <div class="space-y-2">
      <For each={items()}>
        {(alarm) => (
          <div class="bg-white/70 border border-white/70 shadow shadow-amber-900/5 rounded-2xl px-4 py-3 backdrop-blur-sm">
            <div class="flex items-center gap-3">
              <span class="w-4 flex-shrink-0 flex items-center justify-center text-amber-600">
                <span class="text-lg">⏰</span>
              </span>
              <div class="flex-1 min-w-0">
                <span class="text-sm font-semibold text-stone-800 block truncate">
                  {alarm.name}
                </span>
                <span class="text-xs text-stone-500">
                  {formatTime(alarm.time)}
                </span>
              </div>
              <Show when={alarm.url}>
                <a
                  class="flex items-center gap-1 text-xs font-semibold text-amber-700 hover:text-amber-800"
                  href={alarm.url}
                  target="_blank"
                  rel="noreferrer"
                  aria-label="Open alarm link"
                >
                  <span>Open</span>
                  <Icon
                    icon={faArrowUpRightFromSquare}
                    class="w-3 h-3 fill-amber-700"
                  />
                </a>
              </Show>
              <Show when={props.onRemove}>
                <button
                  type="button"
                  onClick={() => props.onRemove?.(alarm)}
                  class="ml-1 inline-flex items-center justify-center w-8 h-8 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-700 transition hover:bg-amber-100/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200"
                  aria-label="Remove alarm"
                  title="Remove alarm"
                >
                  <Icon icon={faTrash} class="w-3.5 h-3.5 fill-amber-700" />
                </button>
              </Show>
            </div>
          </div>
        )}
      </For>
    </div>
  );
};

export default ReadOnlyAlarmList;
