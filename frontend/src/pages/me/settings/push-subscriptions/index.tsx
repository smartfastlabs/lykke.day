import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import { pushAPI } from "@/utils/api";
import PushSubscriptionList from "@/components/push-subscriptions/List";

const PushSubscriptionsPage: Component = () => {
  const navigate = useNavigate();
  const [subscriptions] = createResource(pushAPI.getSubscriptions);

  const handleNavigate = (id?: string) => {
    if (!id) return;
    navigate(`/me/settings/push-subscriptions/${id}`);
  };

  return (
    <SettingsPage heading="Push Subscriptions">
      <Show
        when={subscriptions()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <PushSubscriptionList
          subscriptions={subscriptions()!}
          onItemClick={(subscription) => handleNavigate(subscription.id)}
        />
      </Show>
    </SettingsPage>
  );
};

export default PushSubscriptionsPage;

