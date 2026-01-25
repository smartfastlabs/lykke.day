import { useParams } from "@solidjs/router";
import { Component, Show, createMemo, createResource } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import { brainDumpAPI } from "@/utils/api";
import type { BrainDumpItem, LLMRunResultSnapshot } from "@/types/api";

const safeStringify = (value: unknown): string => {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
};

const formatDateTime = (value?: string | null): string | null => {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

const TodayBrainDumpDetailPage: Component = () => {
  const params = useParams();
  const [brainDump] = createResource<BrainDumpItem | undefined, string>(
    () => params.id,
    (id) => brainDumpAPI.get(id)
  );

  const llmSnapshot = createMemo(() => {
    const current = brainDump();
    if (!current?.llm_run_result) return null;
    return current.llm_run_result as LLMRunResultSnapshot;
  });

  return (
    <SettingsPage
      heading="Brain Dump Details"
      bottomLink={{
        label: "Back to brain dumps",
        url: "/me/today/brain-dumps",
      }}
    >
      <Show
        when={brainDump()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        {(current) => (
          <div class="space-y-6">
            <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-3">
              <div class="flex flex-wrap items-center gap-3 text-sm text-stone-600">
                <span class="font-semibold text-stone-800">Brain Dump</span>
                <span class="text-stone-300">•</span>
                <span class="uppercase tracking-wide">{current().status}</span>
                <span class="text-stone-300">•</span>
                <span class="uppercase tracking-wide text-amber-700/80">
                  {current().type}
                </span>
              </div>
              <Show when={current().created_at}>
                <div class="text-xs text-stone-500">
                  Added {formatDateTime(current().created_at)}
                </div>
              </Show>
              <div class="text-xs text-stone-500">Date {current().date}</div>
            </div>

            <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-3">
              <h2 class="text-sm font-semibold text-stone-700">Item Text</h2>
              <p class="text-sm text-stone-700 whitespace-pre-wrap">
                {current().text}
              </p>
            </div>

            <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-3">
              <h2 class="text-sm font-semibold text-stone-700">Raw Item</h2>
              <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                {safeStringify(current())}
              </pre>
            </div>

            <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-4">
              <h2 class="text-sm font-semibold text-stone-700">LLM Snapshot</h2>
              <Show
                when={llmSnapshot()}
                fallback={
                  <div class="text-sm text-stone-500">
                    No LLM snapshot captured for this brain dump item.
                  </div>
                }
              >
                {(snapshot) => (
                  <div class="space-y-4">
                    <div>
                      <div class="text-xs font-semibold text-stone-600 mb-2">
                        Prompt Context
                      </div>
                      <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                        {safeStringify(snapshot().prompt_context ?? {})}
                      </pre>
                    </div>

                    <div>
                      <div class="text-xs font-semibold text-stone-600 mb-2">
                        Tool Calls
                      </div>
                      <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                        {safeStringify(snapshot().tool_calls ?? [])}
                      </pre>
                    </div>

                    <div>
                      <div class="text-xs font-semibold text-stone-600 mb-2">
                        System Prompt
                      </div>
                      <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                        {snapshot().system_prompt ?? ""}
                      </pre>
                    </div>

                    <div>
                      <div class="text-xs font-semibold text-stone-600 mb-2">
                        Context Prompt
                      </div>
                      <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                        {snapshot().context_prompt ?? ""}
                      </pre>
                    </div>

                    <div>
                      <div class="text-xs font-semibold text-stone-600 mb-2">
                        Ask Prompt
                      </div>
                      <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                        {snapshot().ask_prompt ?? ""}
                      </pre>
                    </div>

                    <div>
                      <div class="text-xs font-semibold text-stone-600 mb-2">
                        Tools Prompt
                      </div>
                      <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                        {snapshot().tools_prompt ?? ""}
                      </pre>
                    </div>

                    <div>
                      <div class="text-xs font-semibold text-stone-600 mb-2">
                        Referenced Entities
                      </div>
                      <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                        {safeStringify(snapshot().referenced_entities ?? [])}
                      </pre>
                    </div>

                    <div>
                      <div class="text-xs font-semibold text-stone-600 mb-2">
                        Raw Snapshot
                      </div>
                      <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
                        {safeStringify(snapshot())}
                      </pre>
                    </div>
                  </div>
                )}
              </Show>
            </div>
          </div>
        )}
      </Show>
    </SettingsPage>
  );
};

export default TodayBrainDumpDetailPage;
