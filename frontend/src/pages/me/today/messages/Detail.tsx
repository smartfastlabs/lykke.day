import { useParams } from "@solidjs/router";
import { Component, Show, createMemo, onMount } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import { useStreamingData } from "@/providers/streamingData";
import type { Message } from "@/types/api";

const safeStringify = (value: unknown): string => {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
};

const formatDateTime = (value: string): string => {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

const TodayMessageDetailPage: Component = () => {
  const params = useParams();
  const { messages, messagesLoading, loadMessages } = useStreamingData();

  onMount(() => {
    void loadMessages();
  });

  const message = createMemo<Message | undefined>(() => {
    if (!params.id) return undefined;
    return messages().find((item) => item.id === params.id);
  });

  return (
    <SettingsPage
      heading="Message Details"
      bottomLink={{
        label: "Back to messages",
        url: "/me/today/messages",
      }}
    >
      <Show
        when={message()}
        fallback={
          <div class="text-center text-gray-500 py-8">
            {messagesLoading() ? "Loading..." : "Message not found."}
          </div>
        }
      >
        {(current) => (
          <div class="space-y-6">
            <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-3">
              <div class="flex flex-wrap items-center gap-3 text-sm text-stone-600">
                <span class="font-semibold text-stone-800">
                  {current().role || "message"}
                </span>
                <Show when={current().triggered_by}>
                  <span class="text-stone-300">•</span>
                  <span>{current().triggered_by}</span>
                </Show>
              </div>
              <div class="text-xs text-stone-500">
                Created {formatDateTime(current().created_at)}
              </div>
            </div>

            <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-3">
              <h2 class="text-sm font-semibold text-stone-700">Content</h2>
              <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                {current().content}
              </pre>
            </div>

            <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-3">
              <h2 class="text-sm font-semibold text-stone-700">Meta</h2>
              <details class="rounded-xl border border-stone-200/80 bg-white/70 p-4">
                <summary class="cursor-pointer text-xs font-semibold text-stone-600">
                  View meta JSON
                </summary>
                <pre class="mt-3 rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                  {safeStringify(current().meta ?? {})}
                </pre>
              </details>
            </div>
          </div>
        )}
      </Show>
    </SettingsPage>
  );
};

export default TodayMessageDetailPage;
