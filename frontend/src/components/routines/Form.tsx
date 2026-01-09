import { Component, JSX, Show, createEffect, createSignal } from "solid-js";
import { Routine, RoutineSchedule, TaskCategory, RoutineTask } from "@/types/api";
import { ALL_TASK_CATEGORIES } from "@/types/api/constants";
import {
  FormError,
  Input,
  Select,
  SubmitButton,
  TextArea,
} from "@/components/forms";
import RoutineScheduleForm from "./RoutineScheduleForm";

interface FormProps {
  onSubmit: (routine: Partial<Routine>) => Promise<void>;
  onChange?: (routine: Partial<Routine>) => void;
  isLoading?: boolean;
  error?: string;
  initialData?: Routine;
  tasks?: RoutineTask[];
  beforeSubmit?: JSX.Element;
}

const RoutineForm: Component<FormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [description, setDescription] = createSignal(
    props.initialData?.description ?? ""
  );
  const [category, setCategory] = createSignal<TaskCategory>(
    props.initialData?.category ?? "HYGIENE"
  );
  const [routineSchedule, setRoutineSchedule] = createSignal<RoutineSchedule>(
    props.initialData?.routine_schedule ?? {
      frequency: "DAILY",
      weekdays: null,
      day_number: null,
    }
  );

  const buildRoutine = (): Partial<Routine> => ({
    name: name().trim(),
    description: description().trim() || "",
    category: category(),
    routine_schedule: routineSchedule(),
    tasks: props.tasks ?? props.initialData?.tasks ?? [],
  });

  createEffect(() => {
    props.onChange?.(buildRoutine());
  });

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    await props.onSubmit(buildRoutine());
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

      <RoutineScheduleForm
        schedule={routineSchedule()}
        onScheduleChange={setRoutineSchedule}
      />

      <FormError error={props.error} />

      <Show when={props.beforeSubmit}>{props.beforeSubmit}</Show>

      <SubmitButton
        isLoading={props.isLoading}
        loadingText={isUpdate ? "Updating..." : "Creating..."}
        text={isUpdate ? "Update Routine" : "Create Routine"}
      />
    </form>
  );
};

export default RoutineForm;
