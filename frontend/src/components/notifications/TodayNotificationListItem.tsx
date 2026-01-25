import { Component, Show, createMemo } from "solid-js";
import { PushNotification } from "@/types/api";

type NotificationPayload = {
  title?: string;
  body?: string;
  [key: string]: unknown;
};

const parsePayload = (content: string): NotificationPayload | null => {
  try {
    const parsed = JSON.parse(content);
    if (parsed && typeof parsed === "object") {
      return parsed as NotificationPayload;
    }
  } catch {
    return null;
  }
  return null;
};

const formatTime = (value: string): string => {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
};

interface ListItemProps {
  notification: PushNotification;
}

const TodayNotificationListItem: Component<ListItemProps> = (props) => {
  const payload = createMemo(() => parsePayload(props.notification.content));
  const title = createMemo(() => {
    const message = props.notification.message?.trim();
    return (
      message ||
      payload()?.title?.toString().trim() ||
      "Notification"
    );
  });
  const subtitle = createMemo(() => {
    return (
      payload()?.body?.toString().trim() ||
      props.notification.triggered_by ||
      props.notification.status
    );
  });

  return (
    <div class="flex items-start gap-4">
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm font-semibold text-stone-700 block truncate">
            {title()}
          </span>
          <span class="text-[11px] text-stone-500 whitespace-nowrap">
            {formatTime(props.notification.sent_at)}
          </span>
        </div>
        <div class="flex flex-wrap items-center gap-2 text-xs text-stone-500 mt-1">
          <span class="truncate">{subtitle()}</span>
          <span class="text-stone-300">•</span>
          <span class="uppercase tracking-wide">{props.notification.status}</span>
          <Show when={props.notification.priority}>
            <span class="text-stone-300">•</span>
            <span class="uppercase tracking-wide text-amber-700/80">
              {props.notification.priority}
            </span>
          </Show>
        </div>
      </div>
    </div>
  );
};

export default TodayNotificationListItem;
