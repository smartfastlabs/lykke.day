import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createMemo, createResource, createSignal } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import PushSubscriptionForm from "@/components/push-subscriptions/Form";
import { pushAPI } from "@/utils/api";
import { PushSubscription } from "@/types/api";

const PushSubscriptionDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [isDirty, setIsDirty] = createSignal(false);

  const [subscription] = createResource<PushSubscription | undefined, string>(
    () => params.id,
    async (id) => pushAPI.get(id)
  );

  const serializeSubscription = (value: Partial<PushSubscription>) =>
    JSON.stringify({
      device_name: (value.device_name ?? "").trim(),
    });

  const initialSignature = createMemo(() => {
    const current = subscription();
    if (!current) return null;
    return serializeSubscription(current);
  });

  const handleFormChange = (value: Partial<PushSubscription>) => {
    const baseline = initialSignature();
    if (!baseline) return;
    setIsDirty(serializeSubscription(value) !== baseline);
  };

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
        <SettingsPage
          heading="Edit Push Subscription"
          bottomLink={{
            label: "Back to Push Subscriptions",
            url: "/me/settings/notifications/push",
          }}
        >
          <div class="space-y-6">
            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Push Subscription
                  </div>
                  <div class="text-lg font-semibold text-stone-800">
                    {current().device_name || "Untitled device"}
                  </div>
                  <Show
                    when={isDirty()}
                    fallback={<div class="text-xs text-stone-400">All changes saved</div>}
                  >
                    <div class="inline-flex items-center gap-2 text-xs font-medium text-amber-700">
                      <span class="h-2 w-2 rounded-full bg-amber-500" />
                      Unsaved changes
                    </div>
                  </Show>
                </div>
                <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <button
                    type="submit"
                    form="push-subscription-form"
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full bg-stone-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isLoading() ? "Saving..." : "Save changes"}
                  </button>
                  <button
                    type="button"
                    onClick={handleDelete}
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full border border-stone-200 bg-white px-5 py-3 text-sm font-semibold text-stone-600 shadow-sm transition hover:border-stone-300 hover:text-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Delete subscription
                  </button>
                </div>
              </div>
            </div>

            <PushSubscriptionForm
              formId="push-subscription-form"
              initialData={current()}
              onSubmit={handleUpdate}
              onChange={handleFormChange}
              isLoading={isLoading()}
              error={error()}
              showSubmitButton={false}
            />
          </div>
        </SettingsPage>
      )}
    </Show>
  );
};

export default PushSubscriptionDetailPage;

