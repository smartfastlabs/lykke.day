import { Component, createSignal } from "solid-js";
import { Calendar } from "@/types/api";
import { FormError, Input, Select, SubmitButton } from "@/components/forms";

const EVENT_CATEGORY_OPTIONS = ["WORK", "PERSONAL", "FAMILY", "SOCIAL", "OTHER"] as const;
type EventCategory = (typeof EVENT_CATEGORY_OPTIONS)[number];

export type CalendarWithCategory = Calendar & {
  default_event_category?: EventCategory | null;
};

interface CalendarFormProps {
  onSubmit: (calendar: Partial<CalendarWithCategory>) => Promise<void>;
  initialData?: CalendarWithCategory;
  isLoading?: boolean;
  error?: string;
}

const CalendarForm: Component<CalendarFormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [authTokenId, setAuthTokenId] = createSignal(props.initialData?.auth_token_id ?? "");
  const [defaultEventCategory, setDefaultEventCategory] = createSignal<EventCategory | "">(
    props.initialData?.default_event_category ?? ""
  );

  const handleSubmit = async (e: Event) => {
    e.preventDefault();

    await props.onSubmit({
      name: name().trim(),
      auth_token_id: authTokenId().trim() || undefined,
      default_event_category: (defaultEventCategory() || undefined) as
        | EventCategory
        | undefined,
    });
  };

  const isUpdate = !!props.initialData;

  return (
    <form onSubmit={handleSubmit} class="space-y-6">
      <Input id="name" placeholder="Name" value={name} onChange={setName} required />

      <Input
        id="authTokenId"
        placeholder="Auth Token ID"
        value={authTokenId}
        onChange={setAuthTokenId}
      />

      <Select<EventCategory | "">
        id="defaultEventCategory"
        value={defaultEventCategory}
        onChange={setDefaultEventCategory}
        options={[...EVENT_CATEGORY_OPTIONS]}
        placeholder="Default Event Category (optional)"
      />

      <FormError error={props.error} />

      <SubmitButton
        isLoading={props.isLoading}
        loadingText={isUpdate ? "Updating..." : "Saving..."}
        text={isUpdate ? "Update Calendar" : "Save Calendar"}
      />
    </form>
  );
};

export default CalendarForm;

