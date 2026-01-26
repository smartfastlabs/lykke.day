import { Component, createEffect, createSignal } from "solid-js";
import { Trigger } from "@/types/api";
import { Input, TextArea, SubmitButton, FormError } from "@/components/forms";

interface FormProps {
  onSubmit: (trigger: Partial<Trigger>) => Promise<void>;
  onChange?: (trigger: Partial<Trigger>) => void;
  isLoading?: boolean;
  error?: string;
  initialData?: Trigger;
  showSubmitButton?: boolean;
  formId?: string;
  submitText?: string;
  loadingText?: string;
}

const TriggerForm: Component<FormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [description, setDescription] = createSignal(
    props.initialData?.description ?? ""
  );

  const buildTrigger = (): Partial<Trigger> => ({
    name: name().trim(),
    description: description().trim(),
  });

  createEffect(() => {
    props.onChange?.(buildTrigger());
  });

  const handleSubmit = async (event: Event) => {
    event.preventDefault();
    await props.onSubmit(buildTrigger());
  };

  const isUpdate = !!props.initialData;
  const shouldShowSubmit = () => props.showSubmitButton ?? true;
  const submitText = () => props.submitText ?? (isUpdate ? "Update Trigger" : "Create Trigger");
  const loadingText = () => props.loadingText ?? (isUpdate ? "Updating..." : "Creating...");

  return (
    <form id={props.formId} onSubmit={handleSubmit} class="space-y-6">
      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Basics</h2>
          <p class="text-sm text-stone-500">
            Name and describe the moment this trigger captures.
          </p>
        </div>
        <div class="space-y-4">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="trigger-name">
              Name
            </label>
            <Input
              id="trigger-name"
              placeholder="Trigger name"
              value={name}
              onChange={setName}
              required
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="trigger-description">
              Description
            </label>
            <TextArea
              id="trigger-description"
              placeholder="Add a short description"
              value={description}
              onChange={setDescription}
              rows={3}
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

export default TriggerForm;
