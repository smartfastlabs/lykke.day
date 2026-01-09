import { Component, createSignal } from "solid-js";

import { FormError, Input, Select, SubmitButton } from "@/components/forms";
import { CalendarEntrySeries } from "@/types/api";

const EVENT_CATEGORY_OPTIONS = ["WORK", "PERSONAL", "FAMILY", "SOCIAL", "OTHER"] as const;
type EventCategory = (typeof EVENT_CATEGORY_OPTIONS)[number];

interface RecurringEventSeriesFormProps {
  onSubmit: (series: Partial<CalendarEntrySeries>) => Promise<void>;
  initialData?: CalendarEntrySeries;
  isLoading?: boolean;
  error?: string;
}

const RecurringEventSeriesForm: Component<RecurringEventSeriesFormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [eventCategory, setEventCategory] = createSignal<EventCategory | "">(
    (props.initialData?.event_category as EventCategory | null) ?? ""
  );

  const handleSubmit = async (e: Event) => {
    e.preventDefault();

    await props.onSubmit({
      name: name().trim(),
      event_category: (eventCategory() || undefined) as EventCategory | undefined,
    });
  };

  const isUpdate = !!props.initialData;

  return (
    <form onSubmit={handleSubmit} class="space-y-6">
      <Input id="name" placeholder="Name" value={name} onChange={setName} required />

      <Select<EventCategory | "">
        id="eventCategory"
        value={eventCategory}
        onChange={setEventCategory}
        options={EVENT_CATEGORY_OPTIONS}
        placeholder="Event Category (optional)"
      />

      <FormError error={props.error} />

      <SubmitButton
        isLoading={props.isLoading}
        loadingText={isUpdate ? "Updating..." : "Saving..."}
        text={isUpdate ? "Update Series" : "Save Series"}
      />
    </form>
  );
};

export default RecurringEventSeriesForm;


