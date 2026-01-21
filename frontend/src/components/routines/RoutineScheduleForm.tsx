import { Component, createSignal, Show, For, Setter, untrack, createMemo } from "solid-js";
import { RecurrenceSchedule, TaskFrequency, DayOfWeek } from "@/types/api";
import { ALL_TASK_FREQUENCIES } from "@/types/api/constants";
import { Select, Input } from "@/components/forms";

// Simple Label component
const Label: Component<{ for: string; children: string }> = (props) => (
  <label for={props.for} class="block text-sm font-medium text-gray-700 mb-1">
    {props.children}
  </label>
);

interface RoutineScheduleFormProps {
  schedule: RecurrenceSchedule | null;
  onScheduleChange: (schedule: RecurrenceSchedule | null) => void;
  label?: string;
  showOptionalToggle?: boolean;
}

const DAYS_OF_WEEK = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
] as const;

const RoutineScheduleForm: Component<RoutineScheduleFormProps> = (props) => {
  // Initialize signals from props (signals are initialized once, so we use untrack)
  const [hasSchedule, setHasSchedule] = createSignal<boolean>(
    untrack(() => props.schedule !== null)
  );
  const [frequency, setFrequency] = createSignal<TaskFrequency>(
    untrack(() => props.schedule?.frequency ?? "DAILY")
  );
  const [weekdays, setWeekdays] = createSignal<DayOfWeek[]>(
    untrack(() => props.schedule?.weekdays ?? [])
  );
  const [dayNumber, setDayNumber] = createSignal<number | null>(
    untrack(() => props.schedule?.day_number ?? null)
  );
  
  // Update when props.schedule changes (for when form is opened with existing schedule)
  createMemo(() => {
    const schedule = props.schedule;
    if (schedule !== null) {
      setHasSchedule(true);
      setFrequency(schedule.frequency);
      setWeekdays(schedule.weekdays ?? []);
      setDayNumber(schedule.day_number ?? null);
    } else if (!props.showOptionalToggle) {
      // If not optional, keep the schedule (for routine schedule form)
      setHasSchedule(true);
    } else {
      // If optional and null, disable
      setHasSchedule(false);
    }
  });

  const handleFrequencyChange = (newFrequency: TaskFrequency) => {
    setFrequency(newFrequency);
    
    // Prepare the updated schedule
    let updatedWeekdays: DayOfWeek[] | null = null;
    let updatedDayNumber: number | null = null;
    
    // Handle weekdays - only keep if CUSTOM_WEEKLY
    if (newFrequency === "CUSTOM_WEEKLY") {
      updatedWeekdays = weekdays().length > 0 ? weekdays() : null;
    } else {
      setWeekdays([]);
    }
    
    // Handle day_number - only keep if MONTHLY or YEARLY
    if (newFrequency === "MONTHLY" || newFrequency === "YEARLY") {
      updatedDayNumber = dayNumber();
    } else {
      setDayNumber(null);
    }
    
    // Update parent - only send schedule if hasSchedule is true
    if (hasSchedule()) {
      props.onScheduleChange({
        frequency: newFrequency,
        weekdays: updatedWeekdays,
        day_number: updatedDayNumber,
      });
    }
  };

  const toggleWeekday = (day: DayOfWeek) => {
    const current = weekdays();
    const newWeekdays = current.includes(day)
      ? current.filter((d) => d !== day)
      : [...current, day].sort((a, b) => a - b);
    
    setWeekdays(newWeekdays);
    if (hasSchedule()) {
      props.onScheduleChange({
        frequency: frequency(),
        weekdays: newWeekdays.length > 0 ? newWeekdays : null,
        day_number: dayNumber(),
      });
    }
  };

  const handleDayNumberChange: Setter<string> = (value) => {
    const actualValue = typeof value === 'function' ? value(dayNumber()?.toString() ?? "") : value;
    const num = actualValue === "" ? null : parseInt(actualValue, 10);
    if (num !== null && (isNaN(num) || num < 1)) {
      return; // Invalid input
    }
    
    const maxValue = frequency() === "MONTHLY" ? 31 : 365;
    const finalValue = num !== null && num > maxValue ? maxValue : num;
    
    setDayNumber(finalValue);
    if (hasSchedule()) {
      props.onScheduleChange({
        frequency: frequency(),
        weekdays: weekdays().length > 0 ? weekdays() : null,
        day_number: finalValue,
      });
    }
  };

  const handleToggleSchedule = (enabled: boolean) => {
    setHasSchedule(enabled);
    if (enabled) {
      // When enabling, create a default schedule
      props.onScheduleChange({
        frequency: frequency(),
        weekdays: weekdays().length > 0 ? weekdays() : null,
        day_number: dayNumber(),
      });
    } else {
      // When disabling, clear the schedule
      props.onScheduleChange(null);
    }
  };

  const requiresWeekdays = () => frequency() === "CUSTOM_WEEKLY";
  const requiresDayNumber = () =>
    frequency() === "MONTHLY" || frequency() === "YEARLY";

  return (
    <div class="space-y-4">
      <Show when={props.showOptionalToggle}>
        <div class="flex items-center space-x-2">
          <input
            type="checkbox"
            id="has-schedule"
            checked={hasSchedule()}
            onChange={(e) => handleToggleSchedule(e.currentTarget.checked)}
            class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label for="has-schedule" class="text-sm font-medium text-gray-700">
            {props.label || "Set custom schedule for this task"}
          </label>
        </div>
      </Show>
      <Show when={!props.showOptionalToggle || hasSchedule()}>
        <div>
          <Label for="frequency">{props.label || "Frequency"}</Label>
          <Select
            id="frequency"
            placeholder="Select frequency"
            value={frequency}
            onChange={handleFrequencyChange}
            options={ALL_TASK_FREQUENCIES}
            required
          />
        </div>

        <Show when={requiresWeekdays()}>
        <div>
          <Label for="weekdays">Days of Week</Label>
          <div class="mt-2 space-y-2">
            <For each={DAYS_OF_WEEK}>
              {(day) => (
                <label class="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={weekdays().includes(day.value as DayOfWeek)}
                    onChange={() => toggleWeekday(day.value as DayOfWeek)}
                    class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span class="text-sm text-gray-700">{day.label}</span>
                </label>
              )}
            </For>
          </div>
          {weekdays().length === 0 && (
            <p class="mt-1 text-sm text-amber-600">
              Select at least one day of the week
            </p>
          )}
        </div>
        </Show>

        <Show when={requiresDayNumber()}>
        <div>
          <Label for="day_number">
            {frequency() === "MONTHLY"
              ? "Day of Month (1-31)"
              : "Day of Year (1-365)"}
          </Label>
          <Input
            id="day_number"
            type="number"
            min="1"
            max={frequency() === "MONTHLY" ? "31" : "365"}
            value={() => dayNumber()?.toString() ?? ""}
            onChange={handleDayNumberChange}
            placeholder={
              frequency() === "MONTHLY" ? "Enter day (1-31)" : "Enter day (1-365)"
            }
            required
          />
          <p class="mt-1 text-sm text-gray-500">
            {frequency() === "MONTHLY"
              ? "The day of the month when this routine should occur (e.g., 15 for the 15th of every month)"
              : "The day of the year when this routine should occur (e.g., 1 for January 1st, 365 for December 31st)"}
          </p>
        </div>
        </Show>
      </Show>
    </div>
  );
};

export default RoutineScheduleForm;

