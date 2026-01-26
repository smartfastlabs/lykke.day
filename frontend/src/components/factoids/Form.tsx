import { Component, createEffect, createSignal } from "solid-js";
import {
  Factoid,
  FactoidCriticality,
  FactoidType,
} from "@/types/api";
import { TextArea, Select, SubmitButton, FormError } from "@/components/forms";

interface FormProps {
  onSubmit: (factoid: Partial<Factoid>) => Promise<void>;
  onChange?: (factoid: Partial<Factoid>) => void;
  isLoading?: boolean;
  error?: string;
  initialData?: Factoid;
  showSubmitButton?: boolean;
  formId?: string;
  submitText?: string;
  loadingText?: string;
}

const FACTOID_TYPE_OPTIONS: { value: FactoidType; label: string }[] = [
  { value: "semantic", label: "Semantic" },
  { value: "episodic", label: "Episodic" },
  { value: "procedural", label: "Procedural" },
];

const FACTOID_CRITICALITY_OPTIONS: { value: FactoidCriticality; label: string }[] = [
  { value: "normal", label: "Normal" },
  { value: "important", label: "Important" },
  { value: "critical", label: "Critical" },
];

const FactoidForm: Component<FormProps> = (props) => {
  const [content, setContent] = createSignal(props.initialData?.content ?? "");
  const [factoidType, setFactoidType] = createSignal<FactoidType>(
    props.initialData?.factoid_type ?? "semantic"
  );
  const [criticality, setCriticality] = createSignal<FactoidCriticality>(
    props.initialData?.criticality ?? "normal"
  );

  const buildFactoid = (): Partial<Factoid> => ({
    content: content().trim(),
    factoid_type: factoidType(),
    criticality: criticality(),
    user_confirmed: true,
  });

  createEffect(() => {
    props.onChange?.(buildFactoid());
  });

  const handleSubmit = async (event: Event) => {
    event.preventDefault();
    await props.onSubmit(buildFactoid());
  };

  const isUpdate = !!props.initialData;
  const shouldShowSubmit = () => props.showSubmitButton ?? true;
  const submitText = () => props.submitText ?? (isUpdate ? "Update Factoid" : "Create Factoid");
  const loadingText = () => props.loadingText ?? (isUpdate ? "Updating..." : "Creating...");

  return (
    <form id={props.formId} onSubmit={handleSubmit} class="space-y-6">
      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Factoid</h2>
          <p class="text-sm text-stone-500">Capture a memory, insight, or instruction.</p>
        </div>
        <div class="space-y-4">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="factoid-content">
              Content
            </label>
            <TextArea
              id="factoid-content"
              placeholder="Add the factoid text"
              value={content}
              onChange={setContent}
              rows={4}
              required
            />
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Classification</h2>
          <p class="text-sm text-stone-500">
            Set the type and importance so it shows up in the right places.
          </p>
        </div>
        <div class="rounded-lg border border-amber-100/80 bg-amber-50/60 px-4 py-3 text-xs text-amber-900/80">
          <div class="font-semibold">Factoid types</div>
          <div>Semantic: general facts. Episodic: specific events. Procedural: how-to habits.</div>
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="factoid-type">
              Type
            </label>
            <Select
              id="factoid-type"
              value={factoidType}
              onChange={setFactoidType}
              options={FACTOID_TYPE_OPTIONS}
              required
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="factoid-criticality">
              Criticality
            </label>
            <Select
              id="factoid-criticality"
              value={criticality}
              onChange={setCriticality}
              options={FACTOID_CRITICALITY_OPTIONS}
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

export default FactoidForm;
