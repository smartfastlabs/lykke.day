import { Component, Show, createEffect, createSignal } from "solid-js";
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
  const toInputTime = (value: string | null | undefined): string => {
    if (!value) return "";
    // Backend commonly returns `HH:MM:SS` but <input type="time"> wants `HH:MM` (unless seconds enabled).
    // Also handle cases like `HH:MM` already.
    const parts = value.split(":");
    if (parts.length >= 2) {
      return `${(parts[0] ?? "00").padStart(2, "0")}:${(parts[1] ?? "00").padStart(2, "0")}`;
    }
    return value;
  };

  const toApiTime = (value: string): string => {
    const trimmed = value.trim();
    // Prefer sending `HH:MM:SS` back to match backend serialization.
    return /^\d{2}:\d{2}$/.test(trimmed) ? `${trimmed}:00` : trimmed;
  };

  const [availableTime, setAvailableTime] = createSignal(
    toInputTime(props.initialSchedule?.available_time),
  );
  const [startTime, setStartTime] = createSignal(
    toInputTime(props.initialSchedule?.start_time),
  );
  const [endTime, setEndTime] = createSignal(
    toInputTime(props.initialSchedule?.end_time),
  );
  const [cutoffTime, setCutoffTime] = createSignal(
    toInputTime(props.initialSchedule?.cutoff_time),
  );
  const [error, setError] = createSignal("");

  // When editing different tasks, `initialSchedule` changes but signals previously did not update.
  createEffect(() => {
    setAvailableTime(toInputTime(props.initialSchedule?.available_time));
    setStartTime(toInputTime(props.initialSchedule?.start_time));
    setEndTime(toInputTime(props.initialSchedule?.end_time));
    setCutoffTime(toInputTime(props.initialSchedule?.cutoff_time));
    setError("");
  });

  const validate = (): boolean => {
    setError("");
    // Validation is optional - all fields are optional
    return true;
  };

  const buildTimeWindow = (): TimeWindow | null => {
    const timeWindow: TimeWindow = {
      available_time: availableTime() ? toApiTime(availableTime()) : null,
      start_time: startTime() ? toApiTime(startTime()) : null,
      end_time: endTime() ? toApiTime(endTime()) : null,
      cutoff_time: cutoffTime() ? toApiTime(cutoffTime()) : null,
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
        <div class="space-y-1">
          <div class="text-sm font-medium text-neutral-700">
            Time Window (all optional)
          </div>
          <div class="text-xs text-neutral-500">
            Set an earliest time, a start/end window, and/or a cutoff.
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="time_window_available_time"
            >
              Available time
            </label>
            <Input
              id="time_window_available_time"
              type="time"
              placeholder="Available time"
              value={availableTime}
              onChange={(val) => {
                setAvailableTime(val);
                handleChange();
              }}
            />
            <div class="text-[11px] text-neutral-500">
              Earliest time it can happen (e.g., after 8:00).
            </div>
          </div>

          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="time_window_start_time"
            >
              Start time
            </label>
            <Input
              id="time_window_start_time"
              type="time"
              placeholder="Start time"
              value={startTime}
              onChange={(val) => {
                setStartTime(val);
                handleChange();
              }}
            />
            <div class="text-[11px] text-neutral-500">
              Preferred window start.
            </div>
          </div>

          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="time_window_end_time"
            >
              End time
            </label>
            <Input
              id="time_window_end_time"
              type="time"
              placeholder="End time"
              value={endTime}
              onChange={(val) => {
                setEndTime(val);
                handleChange();
              }}
            />
            <div class="text-[11px] text-neutral-500">
              Preferred window end (deadline if no start time).
            </div>
          </div>

          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="time_window_cutoff_time"
            >
              Cutoff time
            </label>
            <Input
              id="time_window_cutoff_time"
              type="time"
              placeholder="Cutoff time"
              value={cutoffTime}
              onChange={(val) => {
                setCutoffTime(val);
                handleChange();
              }}
            />
            <div class="text-[11px] text-neutral-500">
              Latest acceptable time to do it.
            </div>
          </div>
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
