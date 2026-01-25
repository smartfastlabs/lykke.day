import { Component } from "solid-js";
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

    <JsonDetailsBlock label="Raw Snapshot" value={props.snapshot} />
  </div>
);

export default LLMSnapshotDetails;
