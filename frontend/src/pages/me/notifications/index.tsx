import { createSignal, onMount, Show } from "solid-js";
import { useNavigate } from "@solidjs/router";
import { pushAPI } from "@/utils/api";
import { PushSubscription } from "@/types/api";
import Page from "@/components/shared/layout/page";

export default function NotificationsIndex() {
  const navigate = useNavigate();
  const [subscriptions, setSubscriptions] = createSignal<PushSubscription[]>(
    []
  );
  const [isLoading, setIsLoading] = createSignal(true);
  const [error, setError] = createSignal("");

  const loadSubscriptions = async () => {
    setIsLoading(true);
    setError("");
    try {
      const data = await pushAPI.getSubscriptions();
      setSubscriptions(data);
    } catch (err) {
      setError("Error loading subscriptions");
      console.error("Error loading subscriptions:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (subscriptionId: string) => {
    if (!subscriptionId) {
      setError("Subscription ID is missing");
      return;
    }

    try {
      await pushAPI.deleteSubscription(subscriptionId);
      // Remove the deleted subscription from the list
      setSubscriptions((subs) =>
        subs.filter((sub) => sub.id !== subscriptionId)
      );
    } catch (err) {
      setError("Error deleting subscription");
      console.error("Error deleting subscription:", err);
    }
  };

  onMount(() => {
    loadSubscriptions();
  });

  return (
    <Page>
      <div class="w-full max-w-2xl mx-auto px-6">
        <div class="flex items-center justify-between mb-8">
          <h1 class="text-2xl font-medium text-neutral-900">
            Push Subscriptions
          </h1>
          <button
            onClick={() => navigate("/me/notifications/subscribe")}
            class="px-4 py-2 bg-neutral-900 text-white font-medium rounded-lg hover:bg-neutral-800 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-2 transition-colors"
          >
            Subscribe
          </button>
        </div>

        <Show when={error()}>
          <p class="text-sm text-red-600 text-center mb-4">{error()}</p>
        </Show>

        <Show when={isLoading()}>
          <p class="text-center text-neutral-600">Loading subscriptions...</p>
        </Show>

        <Show when={!isLoading() && subscriptions().length === 0}>
          <p class="text-center text-neutral-600">No subscriptions found.</p>
        </Show>

        <Show when={!isLoading() && subscriptions().length > 0}>
          <div class="space-y-4">
            {subscriptions().map((sub) => (
              <div class="bg-white border border-neutral-300 rounded-lg p-4 flex items-center justify-between">
                <div class="flex-1">
                  <p class="font-medium text-neutral-900">
                    {sub.device_name || "Unknown Device"}
                  </p>
                  <Show when={sub.createdAt}>
                    <p class="text-xs text-neutral-500 mt-1">
                      Created: {new Date(sub.createdAt!).toLocaleString()}
                    </p>
                  </Show>
                </div>
                <button
                  onClick={() => handleDelete(sub.id!)}
                  class="ml-4 px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2 transition-colors"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        </Show>
      </div>
    </Page>
  );
}
