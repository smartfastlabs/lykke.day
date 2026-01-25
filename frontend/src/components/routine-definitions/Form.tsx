import { Component, JSX, Show, createEffect, createSignal } from "solid-js";
import {
  RecurrenceSchedule,
  RoutineDefinition,
  RoutineDefinitionTask,
  TaskCategory,
  TimeWindow,
} from "@/types/api";
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
  onSubmit: (routineDefinition: Partial<RoutineDefinition>) => Promise<void>;
  onChange?: (routineDefinition: Partial<RoutineDefinition>) => void;
  isLoading?: boolean;
  error?: string;
  initialData?: RoutineDefinition;
  tasks?: RoutineDefinitionTask[];
  beforeSubmit?: JSX.Element;
  showSubmitButton?: boolean;
  formId?: string;
  submitText?: string;
  loadingText?: string;
}

const RoutineForm: Component<FormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [description, setDescription] = createSignal(
    props.initialData?.description ?? ""
  );
  const [category, setCategory] = createSignal<TaskCategory>(
    props.initialData?.category ?? "HYGIENE"
  );
  const [routineDefinitionSchedule, setRoutineDefinitionSchedule] =
    createSignal<RecurrenceSchedule>(
      props.initialData?.routine_definition_schedule ?? {
      frequency: "DAILY",
      weekdays: null,
      day_number: null,
      }
    );
  const [timeWindowAvailable, setTimeWindowAvailable] = createSignal(
    props.initialData?.time_window?.available_time ?? ""
  );
  const [timeWindowStart, setTimeWindowStart] = createSignal(
    props.initialData?.time_window?.start_time ?? ""
  );
  const [timeWindowEnd, setTimeWindowEnd] = createSignal(
    props.initialData?.time_window?.end_time ?? ""
  );
  const [timeWindowCutoff, setTimeWindowCutoff] = createSignal(
    props.initialData?.time_window?.cutoff_time ?? ""
  );

  const buildTimeWindow = (): TimeWindow | null => {
    const timeWindow: TimeWindow = {
      available_time: timeWindowAvailable() || null,
      start_time: timeWindowStart() || null,
      end_time: timeWindowEnd() || null,
      cutoff_time: timeWindowCutoff() || null,
    };
    return Object.values(timeWindow).some((value) => value) ? timeWindow : null;
  };

  const buildRoutineDefinition = (): Partial<RoutineDefinition> => ({
    name: name().trim(),
    description: description().trim() || "",
    category: category(),
    routine_definition_schedule: routineDefinitionSchedule(),
    time_window: buildTimeWindow(),
    tasks: props.tasks ?? props.initialData?.tasks ?? [],
  });

  createEffect(() => {
    props.onChange?.(buildRoutineDefinition());
  });

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    await props.onSubmit(buildRoutineDefinition());
  };

  const isUpdate = !!props.initialData;
  const shouldShowSubmit = () => props.showSubmitButton ?? true;
  const submitText = () =>
    props.submitText ??
    (isUpdate ? "Update Routine Definition" : "Create Routine Definition");
  const loadingText = () =>
    props.loadingText ?? (isUpdate ? "Updating..." : "Creating...");

  return (
    <form id={props.formId} onSubmit={handleSubmit} class="space-y-6">
      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Basics</h2>
          <p class="text-sm text-stone-500">Name, description, and category.</p>
        </div>
        <div class="space-y-4">
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
        </div>
      </div>

      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Schedule</h2>
          <p class="text-sm text-stone-500">
            Choose which days this routine should appear.
          </p>
        </div>
        <RoutineScheduleForm
          schedule={routineDefinitionSchedule()}
          onScheduleChange={setRoutineDefinitionSchedule}
        />
      </div>

      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Time Window</h2>
          <p class="text-sm text-stone-500">
            Optional preferred times for this routine.
          </p>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="routine_definition_time_window_available"
            >
              Available time
            </label>
            <Input
              id="routine_definition_time_window_available"
              type="time"
              placeholder="Available time"
              value={timeWindowAvailable}
              onChange={setTimeWindowAvailable}
            />
          </div>
          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="routine_definition_time_window_start"
            >
              Start time
            </label>
            <Input
              id="routine_definition_time_window_start"
              type="time"
              placeholder="Start time"
              value={timeWindowStart}
              onChange={setTimeWindowStart}
            />
          </div>
          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="routine_definition_time_window_end"
            >
              End time
            </label>
            <Input
              id="routine_definition_time_window_end"
              type="time"
              placeholder="End time"
              value={timeWindowEnd}
              onChange={setTimeWindowEnd}
            />
          </div>
          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="routine_definition_time_window_cutoff"
            >
              Cutoff time
            </label>
            <Input
              id="routine_definition_time_window_cutoff"
              type="time"
              placeholder="Cutoff time"
              value={timeWindowCutoff}
              onChange={setTimeWindowCutoff}
            />
          </div>
        </div>
      </div>

      <FormError error={props.error} />

      <Show when={props.beforeSubmit}>{props.beforeSubmit}</Show>

      <Show when={shouldShowSubmit()}>
        <SubmitButton
          isLoading={props.isLoading}
          loadingText={loadingText()}
          text={submitText()}
        />
      </Show>
    </form>
  );
};

export default RoutineForm;
