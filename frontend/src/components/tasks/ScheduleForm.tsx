import { Component, Show, createSignal } from "solid-js";
import { FormError, Input, Select, SubmitButton } from "@/components/forms";
import { TaskSchedule, TimingType } from "@/types/api";

interface TaskScheduleFormProps {
  initialSchedule?: TaskSchedule | null;
  onSubmit: (schedule: TaskSchedule) => Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
  submitText?: string;
}

const TIMING_OPTIONS: TimingType[] = [
  "FIXED_TIME",
  "TIME_WINDOW",
  "DEADLINE",
  "FLEXIBLE",
];

const TaskScheduleForm: Component<TaskScheduleFormProps> = (props) => {
  const [timingType, setTimingType] = createSignal<TimingType>(
    props.initialSchedule?.timing_type ?? "FLEXIBLE"
  );
  const [availableTime, setAvailableTime] = createSignal(
    props.initialSchedule?.available_time ?? ""
  );
  const [startTime, setStartTime] = createSignal(props.initialSchedule?.start_time ?? "");
  const [endTime, setEndTime] = createSignal(props.initialSchedule?.end_time ?? "");
  const [error, setError] = createSignal("");

  const validate = (): boolean => {
    setError("");
    const type = timingType();

    if (type === "FIXED_TIME" && !startTime()) {
      setError("Start time is required for fixed time tasks.");
      return false;
    }
    if (type === "TIME_WINDOW" && (!startTime() || !endTime())) {
      setError("Start and end times are required for a time window.");
      return false;
    }
    if (type === "DEADLINE" && !endTime()) {
      setError("End time is required for a deadline.");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    if (!validate()) return;

    const schedule: TaskSchedule = {
      timing_type: timingType(),
      available_time: availableTime() || null,
      start_time: startTime() || null,
      end_time: endTime() || null,
    };

    await props.onSubmit(schedule);
  };

  return (
    <form class="space-y-4" onSubmit={handleSubmit}>
      <Select
        id="timing_type"
        placeholder="Timing Type"
        value={timingType}
        onChange={setTimingType}
        options={TIMING_OPTIONS}
        required
      />

      <Show when={timingType() === "FLEXIBLE"}>
        <Input
          id="available_time"
          type="time"
          placeholder="Preferred time (optional)"
          value={availableTime}
          onChange={setAvailableTime}
        />
      </Show>

      <Show when={timingType() === "FIXED_TIME" || timingType() === "TIME_WINDOW"}>
        <Input
          id="start_time"
          type="time"
          placeholder="Start time"
          value={startTime}
          onChange={setStartTime}
          required={timingType() !== "FLEXIBLE"}
        />
      </Show>

      <Show when={timingType() === "TIME_WINDOW" || timingType() === "DEADLINE"}>
        <Input
          id="end_time"
          type="time"
          placeholder="End time"
          value={endTime}
          onChange={setEndTime}
          required={timingType() === "TIME_WINDOW" || timingType() === "DEADLINE"}
        />
      </Show>

      <FormError error={error()} />

      <div class="flex items-center gap-3">
        <SubmitButton
          isLoading={props.isLoading}
          loadingText="Saving..."
          text={props.submitText ?? "Save"}
        />
        <Show when={props.onCancel}>
          <button
            type="button"
            class="text-sm text-gray-600 hover:text-gray-800"
            onClick={() => props.onCancel?.()}
            disabled={props.isLoading}
          >
            Cancel
          </button>
        </Show>
      </div>
    </form>
  );
};

export default TaskScheduleForm;

