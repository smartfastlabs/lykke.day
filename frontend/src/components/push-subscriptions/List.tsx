import { Component } from "solid-js";
import { PushSubscription } from "@/types/api";
import SettingsList from "@/components/shared/SettingsList";
import PushSubscriptionListItem from "./ListItem";

interface ListProps {
  subscriptions: PushSubscription[];
  onItemClick: (subscription: PushSubscription) => void;
}

const PushSubscriptionList: Component<ListProps> = (props) => {
  return (
    <SettingsList
      items={props.subscriptions}
      getItemLabel={(subscription) =>
        subscription.device_name || "Unnamed Device"
      }
      renderItem={(subscription) => (
        <PushSubscriptionListItem subscription={subscription} />
      )}
      onItemClick={props.onItemClick}
      searchPlaceholder="Search push subscriptions"
      emptyStateLabel="No push subscriptions yet."
    />
  );
};

export default PushSubscriptionList;

