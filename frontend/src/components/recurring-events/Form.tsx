import { Component, createEffect, createSignal } from "solid-js";

import { FormError, Input, Select, SubmitButton } from "@/components/forms";
import { CalendarEntrySeries } from "@/types/api";

const EVENT_CATEGORY_OPTIONS = ["WORK", "PERSONAL", "FAMILY", "SOCIAL", "OTHER"] as const;
type EventCategory = (typeof EVENT_CATEGORY_OPTIONS)[number];

interface RecurringEventSeriesFormProps {
  onSubmit: (series: Partial<CalendarEntrySeries>) => Promise<void>;
  onChange?: (series: Partial<CalendarEntrySeries>) => void;
  initialData?: CalendarEntrySeries;
  isLoading?: boolean;
  error?: string;
  showSubmitButton?: boolean;
  formId?: string;
  submitText?: string;
  loadingText?: string;
}

const RecurringEventSeriesForm: Component<RecurringEventSeriesFormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [eventCategory, setEventCategory] = createSignal<EventCategory | "">(
    (props.initialData?.event_category as EventCategory | null) ?? ""
  );

  const buildSeries = (): Partial<CalendarEntrySeries> => ({
    name: name().trim(),
    event_category: (eventCategory() || undefined) as EventCategory | undefined,
  });

  createEffect(() => {
    props.onChange?.(buildSeries());
  });

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    await props.onSubmit(buildSeries());
  };

  const isUpdate = !!props.initialData;
  const shouldShowSubmit = () => props.showSubmitButton ?? true;
  const submitText = () => props.submitText ?? (isUpdate ? "Update Series" : "Save Series");
  const loadingText = () => props.loadingText ?? (isUpdate ? "Updating..." : "Saving...");
  const formatOptionLabel = (value: string) =>
    value
      .toLowerCase()
      .replace(/_/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());

  return (
    <form id={props.formId} onSubmit={handleSubmit} class="space-y-6">
      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Basics</h2>
          <p class="text-sm text-stone-500">
            Name the series and optionally set a category.
          </p>
        </div>
        <div class="space-y-4">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="recurring-series-name">
              Name
            </label>
            <Input
              id="recurring-series-name"
              placeholder="Series name"
              value={name}
              onChange={setName}
              required
            />
          </div>

          <div class="space-y-1">
            <label
              class="text-xs font-medium text-neutral-600"
              for="recurring-series-category"
            >
              Event category
            </label>
            <Select<EventCategory | "">
              id="recurring-series-category"
              value={eventCategory}
              onChange={setEventCategory}
              options={[...EVENT_CATEGORY_OPTIONS].map((option) => ({
                value: option,
                label: formatOptionLabel(option),
              }))}
              placeholder="Select category"
            />
          </div>
        </div>
      </div>

      <FormError error={props.error} />

      {shouldShowSubmit() && (
        <SubmitButton
          isLoading={props.isLoading}
          loadingText={loadingText()}
          text={submitText()}
        />
      )}
    </form>
  );
};

export default RecurringEventSeriesForm;


