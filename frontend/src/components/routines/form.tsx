import { Component, createSignal } from "solid-js";
import {
  Routine,
  RoutineSchedule,
  TaskCategory,
  TaskFrequency,
} from "@/types/api";
import {
  ALL_TASK_CATEGORIES,
  ALL_TASK_FREQUENCIES,
} from "@/types/api/constants";
import {
  FormError,
  Input,
  Select,
  SubmitButton,
  TextArea,
} from "@/components/forms";

interface FormProps {
  onSubmit: (routine: Partial<Routine>) => Promise<void>;
  isLoading?: boolean;
  error?: string;
  initialData?: Routine;
}

const RoutineForm: Component<FormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [description, setDescription] = createSignal(
    props.initialData?.description ?? ""
  );
  const [category, setCategory] = createSignal<TaskCategory>(
    props.initialData?.category ?? "HYGIENE"
  );
  const [frequency, setFrequency] = createSignal<TaskFrequency>(
    props.initialData?.routine_schedule.frequency ?? "DAILY"
  );

  const handleSubmit = async (e: Event) => {
    e.preventDefault();

    const routine_schedule: RoutineSchedule = {
      frequency: frequency(),
      weekdays: props.initialData?.routine_schedule.weekdays ?? null,
    };

    const routine: Partial<Routine> = {
      name: name().trim(),
      description: description().trim() || "",
      category: category(),
      routine_schedule,
      tasks: props.initialData?.tasks ?? [],
    };

    await props.onSubmit(routine);
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
        id="category"
        placeholder="Category"
        value={category}
        onChange={setCategory}
        options={ALL_TASK_CATEGORIES}
        required
      />

      <Select
        id="frequency"
        placeholder="Frequency"
        value={frequency}
        onChange={setFrequency}
        options={ALL_TASK_FREQUENCIES}
        required
      />

      <FormError error={props.error} />

      <SubmitButton
        isLoading={props.isLoading}
        loadingText={isUpdate ? "Updating..." : "Creating..."}
        text={isUpdate ? "Update Routine" : "Create Routine"}
      />
    </form>
  );
};

export default RoutineForm;
