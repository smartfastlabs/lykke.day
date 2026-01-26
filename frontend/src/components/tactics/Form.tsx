import { Component, createEffect, createSignal } from "solid-js";
import { Tactic } from "@/types/api";
import { Input, TextArea, SubmitButton, FormError } from "@/components/forms";

interface FormProps {
  onSubmit: (tactic: Partial<Tactic>) => Promise<void>;
  onChange?: (tactic: Partial<Tactic>) => void;
  isLoading?: boolean;
  error?: string;
  initialData?: Tactic;
  showSubmitButton?: boolean;
  formId?: string;
  submitText?: string;
  loadingText?: string;
}

const TacticForm: Component<FormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [description, setDescription] = createSignal(
    props.initialData?.description ?? ""
  );

  const buildTactic = (): Partial<Tactic> => ({
    name: name().trim(),
    description: description().trim(),
  });

  createEffect(() => {
    props.onChange?.(buildTactic());
  });

  const handleSubmit = async (event: Event) => {
    event.preventDefault();
    await props.onSubmit(buildTactic());
  };

  const isUpdate = !!props.initialData;
  const shouldShowSubmit = () => props.showSubmitButton ?? true;
  const submitText = () => props.submitText ?? (isUpdate ? "Update Tactic" : "Create Tactic");
  const loadingText = () => props.loadingText ?? (isUpdate ? "Updating..." : "Creating...");

  return (
    <form id={props.formId} onSubmit={handleSubmit} class="space-y-6">
      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Basics</h2>
          <p class="text-sm text-stone-500">
            Describe the tactic you want to link to a trigger.
          </p>
        </div>
        <div class="space-y-4">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="tactic-name">
              Name
            </label>
            <Input
              id="tactic-name"
              placeholder="Tactic name"
              value={name}
              onChange={setName}
              required
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="tactic-description">
              Description
            </label>
            <TextArea
              id="tactic-description"
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

export default TacticForm;
