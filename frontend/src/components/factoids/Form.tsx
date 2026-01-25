import { Component, createSignal } from "solid-js";
import {
  Factoid,
  FactoidCriticality,
  FactoidType,
} from "@/types/api";
import { TextArea, Select, SubmitButton, FormError } from "@/components/forms";

interface FormProps {
  onSubmit: (factoid: Partial<Factoid>) => Promise<void>;
  isLoading?: boolean;
  error?: string;
  initialData?: Factoid;
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

  const handleSubmit = async (event: Event) => {
    event.preventDefault();
    const factoid: Partial<Factoid> = {
      content: content().trim(),
      factoid_type: factoidType(),
      criticality: criticality(),
      user_confirmed: true,
    };
    await props.onSubmit(factoid);
  };

  const isUpdate = !!props.initialData;

  return (
    <form onSubmit={handleSubmit} class="space-y-6">
      <TextArea
        id="content"
        placeholder="Factoid"
        value={content}
        onChange={setContent}
        rows={4}
        required
      />

      <div class="rounded-lg border border-neutral-200 bg-white/80 px-4 py-3 text-xs text-neutral-600">
        <div class="font-semibold text-neutral-700">Factoid types</div>
        <div>Semantic: general facts. Episodic: specific events. Procedural: how-to habits.</div>
      </div>

      <Select
        id="factoid-type"
        value={factoidType}
        onChange={setFactoidType}
        options={FACTOID_TYPE_OPTIONS}
        required
      />

      <Select
        id="criticality"
        value={criticality}
        onChange={setCriticality}
        options={FACTOID_CRITICALITY_OPTIONS}
        required
      />

      <FormError error={props.error} />

      <SubmitButton
        isLoading={props.isLoading}
        loadingText={isUpdate ? "Updating..." : "Creating..."}
        text={isUpdate ? "Update Factoid" : "Create Factoid"}
      />
    </form>
  );
};

export default FactoidForm;
