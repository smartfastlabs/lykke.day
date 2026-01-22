import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import DetailPage from "@/components/shared/DetailPage";
import PushSubscriptionForm from "@/components/push-subscriptions/Form";
import PushSubscriptionPreview from "@/components/push-subscriptions/Preview";
import { pushAPI } from "@/utils/api";
import { PushSubscription } from "@/types/api";

const PushSubscriptionDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const [subscription] = createResource<PushSubscription | undefined, string>(
    () => params.id,
    async (id) => pushAPI.get(id)
  );

  const handleUpdate = async (
    partialSubscription: Partial<PushSubscription>
  ) => {
    const current = subscription();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await pushAPI.update({
        ...current,
        ...partialSubscription,
        id: current.id,
      });
      navigate("/me/settings/notifications/push");
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to update push subscription";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = subscription();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await pushAPI.deleteSubscription(current.id);
      navigate("/me/settings/notifications/push");
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to delete push subscription";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Show
      when={subscription()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <DetailPage
          heading="Push Subscription"
          bottomLink={{
            label: "Back to Push Subscriptions",
            url: "/me/settings/notifications/push",
          }}
          preview={<PushSubscriptionPreview subscription={current()} />}
          edit={
            <div class="flex flex-col items-center justify-center px-6 py-8">
              <div class="w-full max-w-sm space-y-6">
                <PushSubscriptionForm
                  initialData={current()}
                  onSubmit={handleUpdate}
                  isLoading={isLoading()}
                  error={error()}
                />
              </div>
            </div>
          }
          onDelete={handleDelete}
        />
      )}
    </Show>
  );
};

export default PushSubscriptionDetailPage;

