import { Component, createSignal } from "solid-js";
import { TaskDefinition, TaskType } from "../../types/api";

interface FormProps {
  onSubmit: (taskDefinition: Partial<TaskDefinition>) => Promise<void>;
  isLoading?: boolean;
  error?: string;
  initialData?: TaskDefinition;
}

const TaskDefinitionForm: Component<FormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name || "");
  const [description, setDescription] = createSignal(
    props.initialData?.description || ""
  );
  const [type, setType] = createSignal<TaskType>(
    props.initialData?.type || "CHORE"
  );

  const handleSubmit = async (e: Event) => {
    e.preventDefault();

    const taskDefinition: Partial<TaskDefinition> = {
      name: name().trim(),
      description: description().trim() || "",
      type: type(),
    };

    await props.onSubmit(taskDefinition);
  };

  const taskTypes: TaskType[] = ["MEAL", "EVENT", "CHORE", "ERRAND", "ACTIVITY"];

  return (
    <form onSubmit={handleSubmit} class="space-y-6">
      <div>
        <label for="name" class="sr-only">
          Name
        </label>
        <input
          id="name"
          type="text"
          placeholder="Name"
          value={name()}
          onInput={(e) => setName(e.currentTarget.value)}
          class="w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
          required
        />
      </div>

      <div>
        <label for="description" class="sr-only">
          Description
        </label>
        <textarea
          id="description"
          placeholder="Description (Optional)"
          value={description()}
          onInput={(e) => setDescription(e.currentTarget.value)}
          class="w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
          rows={3}
        />
      </div>

      <div>
        <label for="type" class="sr-only">
          Type
        </label>
        <select
          id="type"
          value={type()}
          onChange={(e) => setType(e.currentTarget.value as TaskType)}
          class="w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
          required
        >
          {taskTypes.map((taskType) => (
            <option value={taskType}>{taskType}</option>
          ))}
        </select>
      </div>

      {props.error && (
        <p class="text-sm text-red-600 text-center">{props.error}</p>
      )}

      <button
        type="submit"
        disabled={props.isLoading}
        class="w-full py-3 bg-neutral-900 text-white font-medium rounded-lg hover:bg-neutral-800 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {props.isLoading
          ? props.initialData
            ? "Updating..."
            : "Creating..."
          : props.initialData
          ? "Update Task Definition"
          : "Create Task Definition"}
      </button>
    </form>
  );
};

export default TaskDefinitionForm;

