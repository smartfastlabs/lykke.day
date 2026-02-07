import { Component, Show, createMemo } from "solid-js";
import type { Message } from "@/types/api";

const formatTime = (value: string): string => {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
};

const truncate = (value: string, maxLength: number): string => {
  const normalized = value.trim().replace(/\s+/g, " ");
  if (normalized.length <= maxLength) return normalized;
  return `${normalized.slice(0, Math.max(0, maxLength - 1)).trimEnd()}…`;
};

interface ListItemProps {
  message: Message;
}

const TodayMessageListItem: Component<ListItemProps> = (props) => {
  const title = createMemo(() => truncate(props.message.content || "Message", 70));
  const subtitle = createMemo(() => {
    const parts: string[] = [];
    if (props.message.role) parts.push(props.message.role);
    if (props.message.triggered_by) parts.push(props.message.triggered_by);
    return parts.join(" • ");
  });

  return (
    <div class="flex items-start gap-4">
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm font-semibold text-stone-700 block truncate">
            {title()}
          </span>
          <span class="text-[11px] text-stone-500 whitespace-nowrap">
            {formatTime(props.message.created_at)}
          </span>
        </div>
        <Show when={subtitle().length > 0}>
          <div class="flex flex-wrap items-center gap-2 text-xs text-stone-500 mt-1">
            <span class="truncate">{subtitle()}</span>
          </div>
        </Show>
      </div>
    </div>
  );
};

export default TodayMessageListItem;
