import { useParams } from "@solidjs/router";
import { Component, Show, createMemo, createSignal, onMount } from "solid-js";
import NotificationReferencedEntitiesView from "@/components/notifications/ReferencedEntitiesView";
import NotificationLLMDebugView from "@/components/notifications/LLMDebugView";
import { useStreamingData } from "@/providers/streamingData";
import { formatNotificationDateTime, parseContent } from "@/utils/notification";
import type { PushNotification } from "@/types/api";
import TodayPageLayout from "@/pages/me/today/Layout";

type ViewMode = "items" | "debug";

const TodayNotificationDetailPage: Component = () => {
  const params = useParams();
  const [viewMode, setViewMode] = createSignal<ViewMode>("items");
  const { notifications, notificationsLoading, loadNotifications } =
    useStreamingData();

  onMount(() => {
    void loadNotifications();
  });

  const notification = createMemo<PushNotification | undefined>(() => {
    if (!params.id) return undefined;
    return notifications().find((item) => item.id === params.id);
  });

  const referencedEntities = createMemo(() => {
    const n = notification();
    return n?.referenced_entities ?? [];
  });

  const getMessageText = (current: PushNotification): string => {
    if (current.message?.trim()) return current.message.trim();
    const payload = parseContent(current.content);
    const body = payload?.body;
    if (typeof body === "string" && body.trim()) return body.trim();
    const title = payload?.title;
    if (typeof title === "string" && title.trim()) return title.trim();
    return "No message content available.";
  };

  return (
    <TodayPageLayout>
      <Show
        when={notification()}
        fallback={
          <div class="rounded-2xl bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 p-6 text-center text-stone-500">
            {notificationsLoading() ? "Loading..." : "Notification not found."}
          </div>
        }
      >
        {(current) => (
          <div class="space-y-4">
            <div class="flex justify-end">
              <button
                type="button"
                onClick={() =>
                  setViewMode(viewMode() === "items" ? "debug" : "items")
                }
                class="text-[11px] uppercase tracking-wide text-amber-700/80 hover:text-amber-800"
              >
                {viewMode() === "items" ? "LLM Debug" : "Back to items"}
              </button>
            </div>

            <Show
              when={viewMode() === "items"}
              fallback={<NotificationLLMDebugView notification={current()} />}
            >
              <div class="space-y-6">
                <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-3">
                  <p class="text-xs uppercase tracking-wide text-amber-700">
                    Message
                  </p>
                  <p class="text-sm text-stone-800 whitespace-pre-wrap">
                    {getMessageText(current())}
                  </p>
                  <div class="flex flex-wrap items-center gap-3 text-xs text-stone-500">
                    <span>Sent {formatNotificationDateTime(current().sent_at)}</span>
                    <span class="text-stone-300">•</span>
                    <span class="uppercase tracking-wide">{current().status}</span>
                    <Show when={current().priority}>
                      <span class="text-stone-300">•</span>
                      <span class="uppercase tracking-wide text-amber-700/80">
                        {current().priority}
                      </span>
                    </Show>
                    <Show when={current().triggered_by}>
                      <span class="text-stone-300">•</span>
                      <span>{current().triggered_by}</span>
                    </Show>
                  </div>
                  <Show when={current().error_message}>
                    <div class="text-xs text-rose-600">
                      Error: {current().error_message}
                    </div>
                  </Show>
                </div>

                <NotificationReferencedEntitiesView
                  referencedEntities={referencedEntities()}
                />
              </div>
            </Show>
          </div>
        )}
      </Show>
    </TodayPageLayout>
  );
};

export default TodayNotificationDetailPage;
