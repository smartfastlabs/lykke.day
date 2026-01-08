import { Component, createSignal } from "solid-js";
import { Calendar } from "@/types/api";
import { FormError, Input, SubmitButton } from "@/components/forms";

interface CalendarFormProps {
  onSubmit: (calendar: Partial<Calendar>) => Promise<void>;
  initialData?: Calendar;
  isLoading?: boolean;
  error?: string;
}

const CalendarForm: Component<CalendarFormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [authTokenId, setAuthTokenId] = createSignal(props.initialData?.auth_token_id ?? "");

  const handleSubmit = async (e: Event) => {
    e.preventDefault();

    await props.onSubmit({
      name: name().trim(),
      auth_token_id: authTokenId().trim() || undefined,
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

