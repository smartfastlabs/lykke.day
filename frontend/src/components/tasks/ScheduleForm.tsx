import { Component, Show, createSignal } from "solid-js";
import { FormError, Input, SubmitButton } from "@/components/forms";
import { TimeWindow } from "@/types/api";

interface TimeWindowFormProps {
  initialSchedule?: TimeWindow | null;
  onSubmit: (timeWindow: TimeWindow | null) => Promise<void>;
  onChange?: (timeWindow: TimeWindow | null) => void;
  onCancel?: () => void;
  isLoading?: boolean;
  submitText?: string;
}

const TimeWindowForm: Component<TimeWindowFormProps> = (props) => {
  const [availableTime, setAvailableTime] = createSignal(
    props.initialSchedule?.available_time ?? ""
  );
  const [startTime, setStartTime] = createSignal(props.initialSchedule?.start_time ?? "");
  const [endTime, setEndTime] = createSignal(props.initialSchedule?.end_time ?? "");
  const [cutoffTime, setCutoffTime] = createSignal(props.initialSchedule?.cutoff_time ?? "");
  const [error, setError] = createSignal("");

  const validate = (): boolean => {
    setError("");
    // Validation is optional - all fields are optional
    return true;
  };

  const buildTimeWindow = (): TimeWindow | null => {
    const timeWindow: TimeWindow = {
      available_time: availableTime() || null,
      start_time: startTime() || null,
      end_time: endTime() || null,
      cutoff_time: cutoffTime() || null,
    };
    // Return null if all fields are empty
    return Object.values(timeWindow).some((value) => value) ? timeWindow : null;
  };

  const handleChange = () => {
    if (props.onChange) {
      props.onChange(buildTimeWindow());
    }
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    if (!validate()) return;
    await props.onSubmit(buildTimeWindow());
  };

  return (
    <form class="space-y-4" onSubmit={handleSubmit}>
      <div class="space-y-2">
        <label class="text-sm font-medium text-gray-700">Time Window (all optional)</label>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <Input
            id="available_time"
            type="time"
            placeholder="Available time"
            value={availableTime}
            onChange={(val) => {
              setAvailableTime(val);
              handleChange();
            }}
          />
          <Input
            id="start_time"
            type="time"
            placeholder="Start time"
            value={startTime}
            onChange={(val) => {
              setStartTime(val);
              handleChange();
            }}
          />
          <Input
            id="end_time"
            type="time"
            placeholder="End time"
            value={endTime}
            onChange={(val) => {
              setEndTime(val);
              handleChange();
            }}
          />
          <Input
            id="cutoff_time"
            type="time"
            placeholder="Cutoff time"
            value={cutoffTime}
            onChange={(val) => {
              setCutoffTime(val);
              handleChange();
            }}
          />
        </div>
      </div>

      <FormError error={error()} />

      <Show when={props.submitText !== ""}>
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
      </Show>
    </form>
  );
};

export default TimeWindowForm;

