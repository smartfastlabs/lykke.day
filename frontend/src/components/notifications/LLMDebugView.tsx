import { Component, Show } from "solid-js";
import LLMSnapshotDetails from "@/components/llm/LLMSnapshotDetails";
import { parseContent, safeStringify } from "@/utils/notification";
import type { LLMRunResultSnapshot, PushNotification } from "@/types/api";

interface Props {
  notification: PushNotification;
}

const NotificationLLMDebugView: Component<Props> = (props) => {
  const contentPayload = () => parseContent(props.notification.content);
  const llmSnapshot = (): LLMRunResultSnapshot | null =>
    props.notification.llm_snapshot
      ? (props.notification.llm_snapshot as LLMRunResultSnapshot)
      : null;

  return (
    <div class="space-y-6">
      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-3">
        <h2 class="text-sm font-semibold text-stone-700">
          Notification Payload
        </h2>
        <details class="rounded-xl border border-stone-200/80 bg-white/70 p-4">
          <summary class="cursor-pointer text-xs font-semibold text-stone-600">
            View payload JSON
          </summary>
          <pre class="mt-3 rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
            {safeStringify(contentPayload() ?? props.notification.content)}
          </pre>
        </details>
      </div>

      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
        <h2 class="text-sm font-semibold text-stone-700">LLM Snapshot</h2>
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
  );
};

export default NotificationLLMDebugView;
