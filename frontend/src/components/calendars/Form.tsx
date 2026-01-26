import { Component, createEffect, createSignal } from "solid-js";
import { Calendar } from "@/types/api";
import { FormError, Input, Select, SubmitButton } from "@/components/forms";

const EVENT_CATEGORY_OPTIONS = [
  "WORK",
  "PERSONAL",
  "FAMILY",
  "SOCIAL",
  "OTHER",
] as const;
type EventCategory = (typeof EVENT_CATEGORY_OPTIONS)[number];

export type CalendarWithCategory = Calendar & {
  default_event_category?: EventCategory | null;
};

interface CalendarFormProps {
  onSubmit: (calendar: Partial<CalendarWithCategory>) => Promise<void>;
  onChange?: (calendar: Partial<CalendarWithCategory>) => void;
  initialData?: CalendarWithCategory;
  isLoading?: boolean;
  error?: string;
  showSubmitButton?: boolean;
  formId?: string;
  submitText?: string;
  loadingText?: string;
}

const CalendarForm: Component<CalendarFormProps> = (props) => {
  const [name, setName] = createSignal(props.initialData?.name ?? "");
  const [authTokenId, setAuthTokenId] = createSignal(
    props.initialData?.auth_token_id ?? ""
  );
  const [defaultEventCategory, setDefaultEventCategory] = createSignal<
    EventCategory | ""
  >(props.initialData?.default_event_category ?? "");

  const buildCalendar = (): Partial<CalendarWithCategory> => ({
    name: name().trim(),
    auth_token_id: authTokenId().trim() || undefined,
    default_event_category: (defaultEventCategory() || undefined) as
      | EventCategory
      | undefined,
  });

  createEffect(() => {
    props.onChange?.(buildCalendar());
  });

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    await props.onSubmit(buildCalendar());
  };

  const isUpdate = !!props.initialData;
  const shouldShowSubmit = () => props.showSubmitButton ?? true;
  const submitText = () => props.submitText ?? (isUpdate ? "Update Calendar" : "Save Calendar");
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
            Name the calendar and set a default category.
          </p>
        </div>
        <div class="space-y-4">
          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="calendar-name">
              Name
            </label>
            <Input
              id="calendar-name"
              placeholder="Calendar name"
              value={name}
              onChange={setName}
              required
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-medium text-neutral-600" for="calendar-category">
              Default event category
            </label>
            <Select<EventCategory | "">
              id="calendar-category"
              value={defaultEventCategory}
              onChange={setDefaultEventCategory}
              options={[...EVENT_CATEGORY_OPTIONS].map((option) => ({
                value: option,
                label: formatOptionLabel(option),
              }))}
              placeholder="Select category"
            />
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Connection</h2>
          <p class="text-sm text-stone-500">
            Optional token for connecting and syncing.
          </p>
        </div>
        <div class="space-y-1">
          <label class="text-xs font-medium text-neutral-600" for="calendar-auth-token">
            Auth token ID
          </label>
          <Input
            id="calendar-auth-token"
            placeholder="Auth token ID"
            value={authTokenId}
            onChange={setAuthTokenId}
          />
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

export default CalendarForm;
