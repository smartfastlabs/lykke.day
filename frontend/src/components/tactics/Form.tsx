import { Component, createSignal } from "solid-js";
import { Tactic } from "@/types/api";
import { Input, TextArea, SubmitButton, FormError } from "@/components/forms";

interface FormProps {
  onSubmit: (tactic: Partial<Tactic>) => Promise<void>;
  isLoading?: boolean;
  error?: string;
  initialData?: Tactic;
}

const TacticForm: Component<FormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [description, setDescription] = createSignal(
    props.initialData?.description ?? ""
  );

  const handleSubmit = async (event: Event) => {
    event.preventDefault();
    const payload: Partial<Tactic> = {
      name: name().trim(),
      description: description().trim(),
    };
    await props.onSubmit(payload);
  };

  const isUpdate = !!props.initialData;

  return (
    <form onSubmit={handleSubmit} class="space-y-6">
      <Input
        id="tactic-name"
        placeholder="Name"
        value={name}
        onChange={setName}
        required
      />

      <TextArea
        id="tactic-description"
        placeholder="Description"
        value={description}
        onChange={setDescription}
        rows={3}
        required
      />

      <FormError error={props.error} />

      <SubmitButton
        isLoading={props.isLoading}
        loadingText={isUpdate ? "Updating..." : "Creating..."}
        text={isUpdate ? "Update Tactic" : "Create Tactic"}
      />
    </form>
  );
};

export default TacticForm;
