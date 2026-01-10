import { Component } from "solid-js";
import { PushSubscription } from "@/types/api";

interface ListItemProps {
  subscription: PushSubscription;
}

const PushSubscriptionListItem: Component<ListItemProps> = (props) => {
  const formatDate = (dateString?: string) => {
    if (!dateString) return "Unknown";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div class="flex items-center gap-4">
      <div class="flex-1 min-w-0">
        <span class="text-sm text-gray-800 block truncate">
          {props.subscription.device_name || "Unnamed Device"}
        </span>
        <span class="text-xs text-gray-500">
          Created {formatDate(props.subscription.createdAt)}
        </span>
      </div>
    </div>
  );
};

export default PushSubscriptionListItem;

