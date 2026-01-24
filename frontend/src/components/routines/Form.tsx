import { Component, JSX, Show, createEffect, createSignal } from "solid-js";
import { Routine, RecurrenceSchedule, TaskCategory, RoutineTask, TimeWindow } from "@/types/api";
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
  const [routineSchedule, setRoutineSchedule] = createSignal<RecurrenceSchedule>(
    props.initialData?.routine_schedule ?? {
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

  const buildRoutine = (): Partial<Routine> => ({
    name: name().trim(),
    description: description().trim() || "",
    category: category(),
    routine_schedule: routineSchedule(),
    time_window: buildTimeWindow(),
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

      <div class="space-y-2">
        <label class="text-sm font-medium text-neutral-700 block">
          Time Window (optional)
        </label>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="routine_time_window_available">
              Available time
            </label>
            <Input
              id="routine_time_window_available"
              type="time"
              placeholder="Available time"
              value={timeWindowAvailable}
              onChange={setTimeWindowAvailable}
            />
          </div>
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="routine_time_window_start">
              Start time
            </label>
            <Input
              id="routine_time_window_start"
              type="time"
              placeholder="Start time"
              value={timeWindowStart}
              onChange={setTimeWindowStart}
            />
          </div>
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="routine_time_window_end">
              End time
            </label>
            <Input
              id="routine_time_window_end"
              type="time"
              placeholder="End time"
              value={timeWindowEnd}
              onChange={setTimeWindowEnd}
            />
          </div>
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="routine_time_window_cutoff">
              Cutoff time
            </label>
            <Input
              id="routine_time_window_cutoff"
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

      <SubmitButton
        isLoading={props.isLoading}
        loadingText={isUpdate ? "Updating..." : "Creating..."}
        text={isUpdate ? "Update Routine" : "Create Routine"}
      />
    </form>
  );
};

export default RoutineForm;
