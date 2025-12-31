import { Component, createSignal } from "solid-js";
import { TaskDefinition, TaskType } from "../../types/api";
import { Input, TextArea, Select, SubmitButton, FormError } from "../forms";

interface FormProps {
  onSubmit: (taskDefinition: Partial<TaskDefinition>) => Promise<void>;
  isLoading?: boolean;
  error?: string;
  initialData?: TaskDefinition;
}

const TASK_TYPES: TaskType[] = ["MEAL", "EVENT", "CHORE", "ERRAND", "ACTIVITY"];

const TaskDefinitionForm: Component<FormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [description, setDescription] = createSignal(props.initialData?.description ?? "");
  const [type, setType] = createSignal<TaskType>(props.initialData?.type ?? "CHORE");

  const handleSubmit = async (e: Event) => {
    e.preventDefault();

    const taskDefinition: Partial<TaskDefinition> = {
      name: name().trim(),
      description: description().trim() || "",
      type: type(),
    };

    await props.onSubmit(taskDefinition);
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
        options={TASK_TYPES}
        required
      />

      <FormError error={props.error} />

      <SubmitButton
        isLoading={props.isLoading}
        loadingText={isUpdate ? "Updating..." : "Creating..."}
        text={isUpdate ? "Update Task Definition" : "Create Task Definition"}
      />
    </form>
  );
};

export default TaskDefinitionForm;
