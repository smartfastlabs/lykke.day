import { For, Show, type Component } from "solid-js";

import type { KioskItem } from "@/features/kiosk/kioskUtils";

export const KioskList: Component<{
  items: KioskItem[];
  emptyLabel: string;
}> = (props) => (
  <Show
    when={props.items.length > 0}
    fallback={<p class="text-xs text-stone-400">No {props.emptyLabel}</p>}
  >
    <div class="space-y-1.5">
      <For each={props.items}>
        {(item) => (
          <div class="flex items-start gap-2 text-sm text-stone-800">
            <span class="w-14 flex-shrink-0 text-[11px] text-stone-500 tabular-nums text-right">
              {item.time ?? ""}
            </span>
            <span class="flex-1 min-w-0 truncate">{item.label}</span>
            <Show when={item.meta}>
              <span class="text-[10px] uppercase tracking-wide text-stone-400">
                {item.meta}
              </span>
            </Show>
          </div>
        )}
      </For>
    </div>
  </Show>
);
