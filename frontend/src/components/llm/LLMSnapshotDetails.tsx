import { Component, Show } from "solid-js";
import type { LLMRunResultSnapshot } from "@/types/api";

type Props = {
  snapshot: LLMRunResultSnapshot;
};

const safeStringify = (value: unknown): string => {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
};

const formatPromptValue = (value?: string | null): string => {
  if (!value) return "(empty)";
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : "(empty)";
};

const JsonDetailsBlock: Component<{
  label: string;
  value: unknown;
  defaultOpen?: boolean;
}> = (props) => (
  <details
    class="rounded-xl border border-stone-200/80 bg-white/70 p-4"
    open={props.defaultOpen}
  >
    <summary class="cursor-pointer text-xs font-semibold text-stone-600">
      {props.label}
    </summary>
    <pre class="mt-3 rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
      {safeStringify(props.value)}
    </pre>
  </details>
);

const PromptDetailsBlock: Component<{
  label: string;
  value?: string | null;
}> = (props) => (
  <div>
    <div class="text-xs font-semibold text-amber-900 mb-2">{props.label}</div>
    <pre class="rounded-xl bg-stone-900/95 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
      {formatPromptValue(props.value)}
    </pre>
  </div>
);

const hasRequestPayload = (snapshot: LLMRunResultSnapshot): boolean =>
  Boolean(
    snapshot.request_messages?.length ||
      snapshot.request_tools?.length ||
      snapshot.request_tool_choice !== undefined ||
      (snapshot.request_model_params &&
        Object.keys(snapshot.request_model_params).length > 0),
  );

const LLMSnapshotDetails: Component<Props> = (props) => (
  <div class="space-y-4">
    <div class="rounded-xl border border-amber-200/80 bg-amber-50/70 p-4 space-y-3">
      <div class="text-sm font-semibold text-amber-900">
        Fully Rendered Prompts
      </div>
      <PromptDetailsBlock label="System Prompt" value={props.snapshot.system_prompt} />
      <PromptDetailsBlock
        label="Context Prompt"
        value={props.snapshot.context_prompt}
      />
      <PromptDetailsBlock label="Ask Prompt" value={props.snapshot.ask_prompt} />
    </div>

    <JsonDetailsBlock
      label="Prompt Context"
      value={props.snapshot.prompt_context ?? {}}
    />
    <JsonDetailsBlock
      label="Tool Calls"
      value={props.snapshot.tool_calls ?? []}
    />
    <JsonDetailsBlock
      label="Referenced Entities"
      value={props.snapshot.referenced_entities ?? []}
    />

    <details class="rounded-xl border border-stone-200/80 bg-white/70 p-4">
      <summary class="cursor-pointer text-xs font-semibold text-stone-600">
        Tools Prompt
      </summary>
      <pre class="mt-3 rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
        {formatPromptValue(props.snapshot.tools_prompt)}
      </pre>
    </details>

    <Show when={hasRequestPayload(props.snapshot)}>
      <div class="rounded-xl border border-emerald-200/80 bg-emerald-50/70 p-4 space-y-3">
        <div class="text-sm font-semibold text-emerald-900">
          LLM Request Payload (Exact)
        </div>
        <p class="text-xs text-stone-600">
          Exactly what was sent to the LLM: messages, tools, tool choice, and
          model params.
        </p>
        <Show when={(props.snapshot.request_messages?.length ?? 0) > 0}>
          <div>
            <div class="text-xs font-semibold text-emerald-900 mb-2">
              Messages
            </div>
            <div class="space-y-2">
              {props.snapshot.request_messages!.map((msg) => (
                <div class="rounded-lg border border-stone-200/80 bg-white/90 p-3">
                  <span class="text-xs font-medium text-stone-500 uppercase">
                    {msg.role}
                  </span>
                  <pre class="mt-1 text-xs text-stone-800 whitespace-pre-wrap break-words">
                    {typeof msg.content === "string"
                      ? msg.content
                      : safeStringify(msg.content)}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </Show>
        <Show when={(props.snapshot.request_tools?.length ?? 0) > 0}>
          <div>
            <div class="text-xs font-semibold text-emerald-900 mb-2">
              Tools
            </div>
            <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
              {safeStringify(props.snapshot.request_tools)}
            </pre>
          </div>
        </Show>
        <Show
          when={
            props.snapshot.request_tool_choice !== undefined &&
            props.snapshot.request_tool_choice !== null
          }
        >
          <div>
            <div class="text-xs font-semibold text-emerald-900 mb-2">
              Tool choice
            </div>
            <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
              {safeStringify(props.snapshot.request_tool_choice)}
            </pre>
          </div>
        </Show>
        <Show
          when={
            props.snapshot.request_model_params &&
            Object.keys(props.snapshot.request_model_params).length > 0
          }
        >
          <div>
            <div class="text-xs font-semibold text-emerald-900 mb-2">
              Model params
            </div>
            <pre class="rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
              {safeStringify(props.snapshot.request_model_params)}
            </pre>
          </div>
        </Show>
        <details class="rounded-xl border border-stone-200/80 bg-white/70 p-4">
          <summary class="cursor-pointer text-xs font-semibold text-stone-600">
            Raw request payload (JSON)
          </summary>
          <pre class="mt-3 rounded-xl bg-stone-900/90 text-amber-100 text-xs p-4 overflow-auto whitespace-pre-wrap">
            {safeStringify({
              request_messages: props.snapshot.request_messages,
              request_tools: props.snapshot.request_tools,
              request_tool_choice: props.snapshot.request_tool_choice,
              request_model_params: props.snapshot.request_model_params,
            })}
          </pre>
        </details>
      </div>
    </Show>

    <JsonDetailsBlock label="Raw Snapshot" value={props.snapshot} />
  </div>
);

export default LLMSnapshotDetails;
