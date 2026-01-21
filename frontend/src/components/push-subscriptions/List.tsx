import { Component } from "solid-js";
import { PushSubscription } from "@/types/api";
import { GenericList } from "@/components/shared/GenericList";
import PushSubscriptionListItem from "./ListItem";

interface ListProps {
  subscriptions: PushSubscription[];
  onItemClick: (subscription: PushSubscription) => void;
}

const PushSubscriptionList: Component<ListProps> = (props) => {
  return (
    <GenericList
      items={props.subscriptions}
      renderItem={(subscription) => (
        <PushSubscriptionListItem subscription={subscription} />
      )}
      onItemClick={props.onItemClick}
    />
  );
};

export default PushSubscriptionList;

