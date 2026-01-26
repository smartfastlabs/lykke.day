import { Component, createEffect, createSignal } from "solid-js";
import { TaskDefinition, TaskType } from "@/types/api";
import { ALL_TASK_TYPES } from "@/types/api/constants";
import { Input, TextArea, Select, SubmitButton, FormError } from "@/components/forms";

interface FormProps {
  onSubmit: (taskDefinition: Partial<TaskDefinition>) => Promise<void>;
  onChange?: (taskDefinition: Partial<TaskDefinition>) => void;
  isLoading?: boolean;
  error?: string;
  initialData?: TaskDefinition;
  showSubmitButton?: boolean;
  formId?: string;
  submitText?: string;
  loadingText?: string;
}

const TaskDefinitionForm: Component<FormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [description, setDescription] = createSignal(props.initialData?.description ?? "");
  const [type, setType] = createSignal<TaskType>(props.initialData?.type ?? "CHORE");

  const buildTaskDefinition = (): Partial<TaskDefinition> => ({
    name: name().trim(),
    description: description().trim() || "",
    type: type(),
  });

  createEffect(() => {
    props.onChange?.(buildTaskDefinition());
  });

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    await props.onSubmit(buildTaskDefinition());
  };

  const isUpdate = !!props.initialData;
  const shouldShowSubmit = () => props.showSubmitButton ?? true;
  const submitText = () =>
    props.submitText ?? (isUpdate ? "Update Task Definition" : "Create Task Definition");
  const loadingText = () =>
    props.loadingText ?? (isUpdate ? "Updating..." : "Creating...");
  const formatOptionLabel = (value: string) =>
    value
      .toLowerCase()
      .replace(/_/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());

  return (
    <form id={props.formId} onSubmit={handleSubmit} class="space-y-6">
      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Basics</h2>
          <p class="text-sm text-stone-500">
            Give this task a name, description, and type.
          </p>
        </div>
        <div class="space-y-4">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="task-definition-name">
              Name
            </label>
            <Input
              id="task-definition-name"
              placeholder="Task name"
              value={name}
              onChange={setName}
              required
            />
          </div>

          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="task-definition-description"
            >
              Description
            </label>
            <TextArea
              id="task-definition-description"
              placeholder="Optional description"
              value={description}
              onChange={setDescription}
              rows={3}
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="task-definition-type">
              Type
            </label>
            <Select
              id="task-definition-type"
              placeholder="Select type"
              value={type}
              onChange={setType}
              options={ALL_TASK_TYPES.map((option) => ({
                value: option,
                label: formatOptionLabel(option),
              }))}
              required
            />
          </div>
        </div>
      </div>

      <FormError error={props.error} />

      {shouldShowSubmit() && (
        <SubmitButton
          isLoading={props.isLoading}
          loadingText={loadingText()}
          text={submitText()}
        />
      )}
    </form>
  );
};

export default TaskDefinitionForm;
