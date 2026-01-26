import { Component, Show, createMemo } from "solid-js";
import { useNavigate } from "@solidjs/router";
import { Icon } from "@/components/shared/Icon";
import { faBell } from "@fortawesome/free-solid-svg-icons";
import type { Alarm } from "@/types/api";
import AlarmList from "@/components/alarms/List";

export interface AlarmsSummaryProps {
  alarms: Alarm[];
  href?: string;
}

export const AlarmsSummary: Component<AlarmsSummaryProps> = (props) => {
  const navigate = useNavigate();
  const hasLink = createMemo(() => Boolean(props.href));

  return (
    <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
      <div class="flex items-center justify-between">
        <Show
          when={hasLink()}
          fallback={
            <div class="flex items-center gap-3 text-left">
              <Icon icon={faBell} class="w-5 h-5 fill-amber-600" />
              <p class="text-xs uppercase tracking-wide text-amber-700">Alarms</p>
            </div>
          }
        >
          <button
            type="button"
            onClick={() => navigate(props.href!)}
            class="flex items-center gap-3 text-left"
            aria-label="See all alarms"
          >
            <Icon icon={faBell} class="w-5 h-5 fill-amber-600" />
            <p class="text-xs uppercase tracking-wide text-amber-700">Alarms</p>
          </button>
        </Show>
      </div>
      <Show when={props.alarms.length > 0}>
        <div class="space-y-1">
          <AlarmList alarms={() => props.alarms} />
        </div>
      </Show>
    </div>
  );
};

export default AlarmsSummary;
