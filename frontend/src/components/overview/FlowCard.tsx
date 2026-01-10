import { Component, For } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import {
  faPersonRunning,
  faCheckCircle,
  faWater,
  faLeaf,
} from "@fortawesome/free-solid-svg-icons";

export interface FlowItem {
  icon: any;
  text: string;
}

export interface FlowCardProps {
  completionDone: number;
  completionTotal: number;
  items?: FlowItem[];
}

export const FlowCard: Component<FlowCardProps> = (props) => (
  <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
    <div class="flex items-center gap-3">
      <Icon icon={faPersonRunning} class="w-5 h-5 fill-amber-600" />
      <p class="text-xs uppercase tracking-wide text-amber-700">Today's flow</p>
    </div>
    <div class="flex items-center justify-between">
      <div>
        <p class="text-3xl font-extrabold text-stone-900">
          {props.completionDone}/{props.completionTotal}
        </p>
        <p class="text-xs text-stone-500">Tasks feeling good</p>
      </div>
      <div class="w-14 h-14 rounded-full bg-amber-100/80 flex items-center justify-center">
        <Icon icon={faCheckCircle} class="w-6 h-6 fill-amber-700" />
      </div>
    </div>
    <div class="space-y-3">
      <For each={props.items || []}>
        {(item) => (
          <div class="flex items-center gap-3">
            <Icon icon={item.icon} class="w-4 h-4 fill-amber-600" />
            <p class="text-sm text-stone-700">{item.text}</p>
          </div>
        )}
      </For>
    </div>
  </div>
);

