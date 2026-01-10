import { Component, createSignal } from "solid-js";
import { PushSubscription } from "@/types/api";
import { Input, Button, FormError } from "@/components/forms";

interface FormProps {
  initialData?: PushSubscription;
  onSubmit: (data: Partial<PushSubscription>) => Promise<void>;
  isLoading: boolean;
  error: string;
}

const PushSubscriptionForm: Component<FormProps> = (props) => {
  const [deviceName, setDeviceName] = createSignal(
    props.initialData?.device_name || ""
  );

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    await props.onSubmit({
      device_name: deviceName().trim() || null,
    });
  };

  return (
    <form onSubmit={handleSubmit} class="space-y-6">
      <Input
        label="Device Name"
        type="text"
        value={deviceName()}
        onInput={(e) => setDeviceName(e.currentTarget.value)}
        placeholder="Enter device name"
      />

      <FormError error={props.error} />

      <Button type="submit" disabled={props.isLoading} fullWidth>
        {props.isLoading ? "Saving..." : "Save Changes"}
      </Button>
    </form>
  );
};

export default PushSubscriptionForm;

