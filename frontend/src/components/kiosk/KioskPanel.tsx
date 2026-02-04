import type { Component, JSX } from "solid-js";
import { Show } from "solid-js";

export const KioskPanel: Component<{
  title: string;
  count?: number;
  children: JSX.Element;
}> = (props) => (
  <div class="min-h-0 rounded-2xl border border-white/70 bg-white/80 p-3 shadow-sm shadow-amber-900/5 backdrop-blur-sm flex flex-col gap-2">
    <div class="flex items-center justify-between text-[11px] uppercase tracking-[0.25em] text-stone-500">
      <span>TITLE:{props.title}</span>
      <Show when={props.count !== undefined}>
        <span class="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700">
          {props.count}
        </span>
      </Show>
    </div>
    <div class="flex-1 min-h-0 overflow-y-auto pr-1">{props.children}</div>
  </div>
);
