import { Component, createEffect, createSignal } from "solid-js";
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
  showSubmitButton?: boolean;
  formId?: string;
  submitText?: string;
  loadingText?: string;
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
  const shouldShowSubmit = () => props.showSubmitButton ?? true;
  const submitText = () =>
    props.submitText ?? (isUpdate ? "Update Time Block" : "Create Time Block");
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
            Name and description so you can spot this quickly.
          </p>
        </div>
        <div class="space-y-4">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="time_block_name">
              Name
            </label>
            <Input
              id="time_block_name"
              placeholder="Time block name"
              value={name}
              onChange={setName}
              required
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="time_block_description">
              Description
            </label>
            <TextArea
              id="time_block_description"
              placeholder="Optional notes for this time block"
              value={description}
              onChange={setDescription}
              rows={3}
            />
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Classification</h2>
          <p class="text-sm text-stone-500">
            Choose a type and category for reporting and grouping.
          </p>
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="time_block_type">
              Type
            </label>
            <Select
              id="time_block_type"
              placeholder="Select type"
              value={type}
              onChange={setType}
              options={ALL_TIME_BLOCK_TYPES.map((option) => ({
                value: option,
                label: formatOptionLabel(option),
              }))}
              required
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="time_block_category">
              Category
            </label>
            <Select
              id="time_block_category"
              placeholder="Select category"
              value={category}
              onChange={setCategory}
              options={ALL_TIME_BLOCK_CATEGORIES.map((option) => ({
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

export default TimeBlockDefinitionForm;

