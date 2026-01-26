import { Component, createEffect, createSignal } from "solid-js";
import { PushSubscription } from "@/types/api";
import { Input, FormError, SubmitButton } from "@/components/forms";

interface FormProps {
  initialData?: PushSubscription;
  onSubmit: (data: Partial<PushSubscription>) => Promise<void>;
  isLoading: boolean;
  error: string;
  onChange?: (data: Partial<PushSubscription>) => void;
  showSubmitButton?: boolean;
  formId?: string;
  submitText?: string;
  loadingText?: string;
}

const PushSubscriptionForm: Component<FormProps> = (props) => {
  const [deviceName, setDeviceName] = createSignal(
    props.initialData?.device_name || ""
  );

  const buildPayload = (): Partial<PushSubscription> => ({
    device_name: deviceName().trim() || null,
  });

  createEffect(() => {
    props.onChange?.(buildPayload());
  });

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    await props.onSubmit(buildPayload());
  };

  const shouldShowSubmit = () => props.showSubmitButton ?? true;
  const submitText = () => props.submitText ?? "Save Changes";
  const loadingText = () => props.loadingText ?? "Saving...";

  return (
    <form id={props.formId} onSubmit={handleSubmit} class="space-y-6">
      <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm space-y-4">
        <div>
          <h2 class="text-lg font-semibold text-stone-800">Device</h2>
          <p class="text-sm text-stone-500">
            Give this subscription a friendly device name.
          </p>
        </div>
        <div class="space-y-1">
          <label class="text-xs font-medium text-neutral-600" for="push-device-name">
            Device name
          </label>
          <Input
            id="push-device-name"
            type="text"
            value={deviceName}
            onChange={setDeviceName}
            placeholder="e.g. Todd's iPhone"
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

export default PushSubscriptionForm;

