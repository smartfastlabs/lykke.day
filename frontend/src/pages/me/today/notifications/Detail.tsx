import { useParams } from "@solidjs/router";
import { Component, Show, createMemo, createResource } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import LLMSnapshotDetails from "@/components/llm/LLMSnapshotDetails";
import { notificationAPI } from "@/utils/api";
import type { LLMRunResultSnapshot, PushNotification } from "@/types/api";

const safeStringify = (value: unknown): string => {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
};

const parseContent = (content: string): Record<string, unknown> | null => {
  try {
    const parsed = JSON.parse(content);
    if (parsed && typeof parsed === "object") {
      return parsed as Record<string, unknown>;
    }
  } catch {
    return null;
  }
  return null;
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

const TodayNotificationDetailPage: Component = () => {
  const params = useParams();
  const [notification] = createResource<PushNotification | undefined, string>(
    () => params.id,
    (id) => notificationAPI.get(id)
  );

  const contentPayload = createMemo(() => {
    const current = notification();
    if (!current) return null;
    return parseContent(current.content);
  });

  const llmSnapshot = createMemo(() => {
    const current = notification();
    if (!current?.llm_snapshot) return null;
    return current.llm_snapshot as LLMRunResultSnapshot;
  });

  return (
    <SettingsPage
      heading="Notification Details"
      bottomLink={{
        label: "Back to notifications",
        url: "/me/today/notifications",
      }}
    >
      <Show
        when={notification()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        {(current) => (
          <div class="space-y-6">
            <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-3">
              <div class="flex flex-wrap items-center gap-3 text-sm text-stone-600">
                <span class="font-semibold text-stone-800">
                  {current().message || "Notification"}
                </span>
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
              <div class="text-xs text-stone-500">
                Sent {formatDateTime(current().sent_at)}
              </div>
              <Show when={current().error_message}>
                <div class="text-xs text-rose-600">
                  Error: {current().error_message}
                </div>
              </Show>
            </div>

            <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-3">
              <h2 class="text-sm font-semibold text-stone-700">
                Notification Payload
              </h2>
              <details class="rounded-xl border border-stone-200/80 bg-white/70 p-4">
                <summary class="cursor-pointer text-xs font-semibold text-stone-600">
                  View payload JSON
                </summary>
                <pre class="mt-3 rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                  {safeStringify(contentPayload() ?? current().content)}
                </pre>
              </details>
            </div>

            <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-4">
              <h2 class="text-sm font-semibold text-stone-700">
                LLM Snapshot
              </h2>
              <Show
                when={llmSnapshot()}
                fallback={
                  <div class="text-sm text-stone-500">
                    No LLM snapshot captured for this notification.
                  </div>
                }
              >
                {(snapshot) => <LLMSnapshotDetails snapshot={snapshot()} />}
              </Show>
            </div>
          </div>
        )}
      </Show>
    </SettingsPage>
  );
};

export default TodayNotificationDetailPage;
