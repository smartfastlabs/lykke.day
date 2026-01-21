import { Component, Show } from "solid-js";
import { PushSubscription } from "@/types/api";

interface PushSubscriptionPreviewProps {
  subscription: PushSubscription;
}

const PushSubscriptionPreview: Component<PushSubscriptionPreviewProps> = (
  props
) => {
  const formatDate = (dateString?: string) => {
    if (!dateString) return "Unknown";
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const truncateEndpoint = (endpoint: string) => {
    if (endpoint.length <= 50) return endpoint;
    return endpoint.substring(0, 47) + "...";
  };

  return (
    <div class="flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-sm space-y-6">
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">
            Subscription Details
          </h2>
          <div class="space-y-3">
            <div>
              <label class="text-sm font-medium text-neutral-500">
                Device Name
              </label>
              <div class="mt-1 text-base text-neutral-900">
                {props.subscription.device_name || "Unnamed Device"}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">
                Endpoint
              </label>
              <div class="mt-1 text-xs text-neutral-700 break-all font-mono">
                {truncateEndpoint(props.subscription.endpoint)}
              </div>
            </div>
            <Show when={props.subscription.created_at}>
              <div>
                <label class="text-sm font-medium text-neutral-500">
                  Created
                </label>
                <div class="mt-1 text-base text-neutral-900">
                  {formatDate(props.subscription.created_at)}
                </div>
              </div>
            </Show>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PushSubscriptionPreview;

