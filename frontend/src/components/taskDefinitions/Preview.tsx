import { Component, Show } from "solid-js";
import { TaskDefinition } from "@/types/api";

interface TaskDefinitionPreviewProps {
  taskDefinition: TaskDefinition;
}

const TaskDefinitionPreview: Component<TaskDefinitionPreviewProps> = (props) => {
  return (
    <div class="flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-sm space-y-6">
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Basic Information</h2>
          <div class="space-y-3">
            <div>
              <label class="text-sm font-medium text-neutral-500">Name</label>
              <div class="mt-1 text-base text-neutral-900">{props.taskDefinition.name}</div>
            </div>
            <Show when={props.taskDefinition.description}>
              <div>
                <label class="text-sm font-medium text-neutral-500">Description</label>
                <div class="mt-1 text-base text-neutral-900">
                  {props.taskDefinition.description}
                </div>
              </div>
            </Show>
            <div>
              <label class="text-sm font-medium text-neutral-500">Type</label>
              <div class="mt-1 text-base text-neutral-900">{props.taskDefinition.type}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskDefinitionPreview;

