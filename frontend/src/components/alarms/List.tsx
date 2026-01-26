import { Component, For, Show } from "solid-js";
import type { Accessor } from "solid-js";
import { Alarm } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import { faArrowUpRightFromSquare } from "@fortawesome/free-solid-svg-icons";

const formatTime = (timeValue: string): string => timeValue.slice(0, 5);

const AlarmItem: Component<{ alarm: Alarm }> = (props) => (
  <div class="flex items-center gap-4 rounded-xl border border-amber-100/80 bg-white/80 px-4 py-3">
    <span class="w-4 flex-shrink-0 flex items-center justify-center text-amber-600">
      <span class="text-lg">⏰</span>
    </span>

    <div class="flex-1 min-w-0">
      <span class="text-sm font-semibold text-stone-800 block truncate">
        {props.alarm.name}
      </span>
      <span class="text-xs text-stone-500">
        {formatTime(props.alarm.time)}
      </span>
    </div>

    <Show when={props.alarm.url}>
      <a
        class="flex items-center gap-1 text-xs font-semibold text-amber-700 hover:text-amber-800"
        href={props.alarm.url}
        target="_blank"
        rel="noreferrer"
        aria-label="Open alarm link"
      >
        <span>Open</span>
        <Icon icon={faArrowUpRightFromSquare} class="w-3 h-3 fill-amber-700" />
      </a>
    </Show>
  </div>
);

interface AlarmListProps {
  alarms: Accessor<Alarm[]>;
}

const AlarmList: Component<AlarmListProps> = (props) => {
  const alarms = () => props.alarms() ?? [];

  return (
    <div class="space-y-2">
      <For each={alarms()}>{(alarm) => <AlarmItem alarm={alarm} />}</For>
    </div>
  );
};

export default AlarmList;
