import { Component } from "solid-js";
import { Factoid } from "@/types/api";

interface FactoidPreviewProps {
  factoid: Factoid;
}

const FactoidPreview: Component<FactoidPreviewProps> = (props) => {
  return (
    <div class="flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-sm space-y-6">
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Factoid</h2>
          <div class="space-y-3">
            <div>
              <label class="text-sm font-medium text-neutral-500">Content</label>
              <div class="mt-1 text-base text-neutral-900">{props.factoid.content}</div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Type</label>
              <div class="mt-1 text-base text-neutral-900">
                {props.factoid.factoid_type}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Criticality</label>
              <div class="mt-1 text-base text-neutral-900">
                {props.factoid.criticality}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FactoidPreview;
