import { Component, Show, createMemo } from "solid-js";
import type { BrainDump } from "@/types/api";

const formatTime = (value?: string | null): string | null => {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
};

interface ListItemProps {
  item: BrainDump;
}

const TodayBrainDumpListItem: Component<ListItemProps> = (props) => {
  const title = createMemo(() => props.item.text.trim() || "Brain dump");
  const createdAt = createMemo(() => formatTime(props.item.created_at));

  return (
    <div class="flex items-start gap-4">
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm font-semibold text-stone-700 block truncate">
            {title()}
          </span>
          <Show when={createdAt()}>
            {(time) => (
              <span class="text-[11px] text-stone-500 whitespace-nowrap">
                {time()}
              </span>
            )}
          </Show>
        </div>
        <div class="flex flex-wrap items-center gap-2 text-xs text-stone-500 mt-1">
          <span class="uppercase tracking-wide">{props.item.status}</span>
          <span class="text-stone-300">•</span>
          <span class="uppercase tracking-wide text-amber-700/80">
            {props.item.type}
          </span>
        </div>
      </div>
    </div>
  );
};

export default TodayBrainDumpListItem;
