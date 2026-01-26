import { Component, Show } from "solid-js";
import { Tactic } from "@/types/api";

interface TacticPreviewProps {
  tactic: Tactic;
}

const TacticPreview: Component<TacticPreviewProps> = (props) => {
  return (
    <div class="flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-sm space-y-6">
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Tactic</h2>
          <div class="space-y-3">
            <div>
              <label class="text-sm font-medium text-neutral-500">Name</label>
              <div class="mt-1 text-base text-neutral-900">
                {props.tactic.name}
              </div>
            </div>
            <Show when={props.tactic.description}>
              <div>
                <label class="text-sm font-medium text-neutral-500">
                  Description
                </label>
                <div class="mt-1 text-base text-neutral-900">
                  {props.tactic.description}
                </div>
              </div>
            </Show>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TacticPreview;
