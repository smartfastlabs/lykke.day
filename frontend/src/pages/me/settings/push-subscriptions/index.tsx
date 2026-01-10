import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import { faBell } from "@fortawesome/free-solid-svg-icons";
import SettingsPage, { ActionButton } from "@/components/shared/SettingsPage";
import { pushAPI } from "@/utils/api";
import PushSubscriptionList from "@/components/push-subscriptions/List";
import ModalPage from "@/components/shared/ModalPage";
import { Input, Button, FormError } from "@/components/forms";

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(buffer)));
}

const PushSubscriptionsPage: Component = () => {
  const navigate = useNavigate();
  const [subscriptions, { refetch }] = createResource(pushAPI.getSubscriptions);
  const [showSubscribeModal, setShowSubscribeModal] = createSignal(false);
  const [deviceName, setDeviceName] = createSignal("");
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleNavigate = (id?: string) => {
    if (!id) return;
    navigate(`/me/settings/push-subscriptions/${id}`);
  };

  const handleSubscribe = async (e: Event) => {
    e.preventDefault();
    setError("");

    if (!deviceName().trim()) {
      setError("Device name is required");
      return;
    }

    if (!("serviceWorker" in navigator)) {
      setError("Service Worker is not supported in this browser");
      return;
    }

    if (!("PushManager" in window)) {
      setError("Push notifications are not supported in this browser");
      return;
    }

    setIsLoading(true);

    try {
      // Request notification permission
      const permission = await Notification.requestPermission();
      
      if (permission !== "granted") {
        setError("Notification permission denied");
        setIsLoading(false);
        return;
      }

      // Get service worker registration
      const registration = await navigator.serviceWorker.ready;

      // Subscribe to push notifications
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey:
          "BNWaFxSOKFUzGfVP5DOYhDSS8Nf2W9ifg4_3pNsfEzDih5CfspqP7-Ncr_9jAuwkd8jaHZPHdc0zIqHE-IPDoF8",
      });

      // Send subscription to backend
      await fetch("/api/push/subscribe/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          device_name: deviceName().trim(),
          endpoint: subscription.endpoint,
          keys: {
            p256dh: arrayBufferToBase64(subscription.getKey("p256dh")!),
            auth: arrayBufferToBase64(subscription.getKey("auth")!),
          },
        }),
      });

      // Reset form and close modal
      setDeviceName("");
      setShowSubscribeModal(false);
      
      // Refresh the subscriptions list
      refetch();
    } catch (err) {
      console.error("Push subscription error:", err);
      setError(
        err instanceof Error ? err.message : "Failed to subscribe to push notifications"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const actionButtons: ActionButton[] = [
    {
      label: "Subscribe",
      icon: faBell,
      onClick: () => setShowSubscribeModal(true),
    },
  ];

  return (
    <>
      <SettingsPage heading="Push Subscriptions" actionButtons={actionButtons}>
        <Show
          when={subscriptions()}
          fallback={
            <div class="text-center text-gray-500 py-8">Loading...</div>
          }
        >
          <PushSubscriptionList
            subscriptions={subscriptions()!}
            onItemClick={(subscription) => handleNavigate(subscription.id)}
          />
        </Show>
      </SettingsPage>

      <Show when={showSubscribeModal()}>
        <ModalPage
          title="Subscribe to Push Notifications"
          onClose={() => {
            setShowSubscribeModal(false);
            setDeviceName("");
            setError("");
          }}
        >
          <form onSubmit={handleSubscribe} class="space-y-6">
            <Input
              id="device-name"
              type="text"
              value={deviceName}
              onChange={setDeviceName}
              placeholder="e.g., My iPhone, Work Laptop"
              required
            />

            <FormError error={error()} />

            <div class="flex gap-3">
              <Button
                type="button"
                onClick={() => {
                  setShowSubscribeModal(false);
                  setDeviceName("");
                  setError("");
                }}
                variant="secondary"
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading()}>
                {isLoading() ? "Subscribing..." : "Subscribe"}
              </Button>
            </div>
          </form>
        </ModalPage>
      </Show>
    </>
  );
};

export default PushSubscriptionsPage;

