import { Component, For, Show } from "solid-js";
import { Tactic, Trigger } from "@/types/api";

interface TriggerPreviewProps {
  trigger: Trigger;
  tactics?: Tactic[];
}

const TriggerPreview: Component<TriggerPreviewProps> = (props) => {
  const tactics = () => props.tactics ?? [];

  return (
    <div class="flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-lg space-y-6">
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Trigger</h2>
          <div class="space-y-3">
            <div>
              <label class="text-sm font-medium text-neutral-500">Name</label>
              <div class="mt-1 text-base text-neutral-900">
                {props.trigger.name}
              </div>
            </div>
            <Show when={props.trigger.description}>
              <div>
                <label class="text-sm font-medium text-neutral-500">
                  Description
                </label>
                <div class="mt-1 text-base text-neutral-900">
                  {props.trigger.description}
                </div>
              </div>
            </Show>
          </div>
        </div>

        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <div>
            <h3 class="text-base font-medium text-neutral-900">Linked tactics</h3>
            <p class="text-sm text-neutral-500">
              Tactics that help when this trigger shows up.
            </p>
          </div>
          <Show
            when={tactics().length > 0}
            fallback={
              <div class="text-sm text-neutral-500">
                No tactics linked yet.
              </div>
            }
          >
            <div class="space-y-2">
              <For each={tactics()}>
                {(tactic) => (
                  <div class="rounded-md border border-neutral-200 px-3 py-2 text-sm text-neutral-800">
                    <div class="font-medium">{tactic.name}</div>
                    <Show when={tactic.description}>
                      <div class="text-xs text-neutral-500">
                        {tactic.description}
                      </div>
                    </Show>
                  </div>
                )}
              </For>
            </div>
          </Show>
        </div>
      </div>
    </div>
  );
};

export default TriggerPreview;
