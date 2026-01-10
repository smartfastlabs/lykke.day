import { Component, createEffect, createSignal, Show } from "solid-js";
import { TimeBlockDefinition, TimeBlockType, TimeBlockCategory } from "@/types/api";
import {
  FormError,
  Input,
  Select,
  SubmitButton,
  TextArea,
} from "@/components/forms";

// All time block types
const ALL_TIME_BLOCK_TYPES: TimeBlockType[] = [
  "WORK",
  "BREAK",
  "MEAL",
  "EXERCISE",
  "COMMUTE",
  "MEETING",
  "FOCUS",
  "ADMIN",
  "CREATIVE",
  "LEARNING",
  "SOCIAL",
  "PERSONAL",
  "ROUTINE",
  "SLEEP",
  "OTHER",
];

// All time block categories
const ALL_TIME_BLOCK_CATEGORIES: TimeBlockCategory[] = [
  "WORK",
  "PROFESSIONAL",
  "MEETING",
  "PERSONAL_CARE",
  "HEALTH",
  "FITNESS",
  "NUTRITION",
  "SLEEP",
  "HOUSEHOLD",
  "CHORES",
  "MAINTENANCE",
  "FAMILY",
  "SOCIAL",
  "RELATIONSHIP",
  "ENTERTAINMENT",
  "HOBBY",
  "RECREATION",
  "EDUCATION",
  "LEARNING",
  "COMMUTE",
  "TRAVEL",
  "PLANNING",
  "ADMIN",
  "OTHER",
];

interface FormProps {
  onSubmit: (timeBlockDefinition: Partial<TimeBlockDefinition>) => Promise<void>;
  onChange?: (timeBlockDefinition: Partial<TimeBlockDefinition>) => void;
  isLoading?: boolean;
  error?: string;
  initialData?: TimeBlockDefinition;
}

const TimeBlockDefinitionForm: Component<FormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [description, setDescription] = createSignal(
    props.initialData?.description ?? ""
  );
  const [type, setType] = createSignal<TimeBlockType>(
    props.initialData?.type ?? "WORK"
  );
  const [category, setCategory] = createSignal<TimeBlockCategory>(
    props.initialData?.category ?? "WORK"
  );

  const buildTimeBlockDefinition = (): Partial<TimeBlockDefinition> => ({
    name: name().trim(),
    description: description().trim() || "",
    type: type(),
    category: category(),
  });

  createEffect(() => {
    props.onChange?.(buildTimeBlockDefinition());
  });

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    await props.onSubmit(buildTimeBlockDefinition());
  };

  const isUpdate = !!props.initialData;

  return (
    <form onSubmit={handleSubmit} class="space-y-6">
      <Input
        id="name"
        placeholder="Name"
        value={name}
        onChange={setName}
        required
      />

      <TextArea
        id="description"
        placeholder="Description (Optional)"
        value={description}
        onChange={setDescription}
        rows={3}
      />

      <Select
        id="type"
        placeholder="Type"
        value={type}
        onChange={setType}
        options={ALL_TIME_BLOCK_TYPES}
        required
      />

      <Select
        id="category"
        placeholder="Category"
        value={category}
        onChange={setCategory}
        options={ALL_TIME_BLOCK_CATEGORIES}
        required
      />

      <FormError error={props.error} />

      <SubmitButton
        isLoading={props.isLoading}
        loadingText={isUpdate ? "Updating..." : "Creating..."}
        text={isUpdate ? "Update Time Block" : "Create Time Block"}
      />
    </form>
  );
};

export default TimeBlockDefinitionForm;

