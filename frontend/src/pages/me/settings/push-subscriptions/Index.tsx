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
  const [isSendingTestPush, setIsSendingTestPush] = createSignal(false);
  const [testPushMessage, setTestPushMessage] = createSignal("");

  const handleNavigate = (id?: string | null) => {
    if (!id) return;
    navigate(`/me/settings/notifications/push/${id}`);
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
    {
      label: isSendingTestPush() ? "Sending..." : "Send Test Push",
      icon: faBell,
      onClick: async () => {
        setTestPushMessage("");
        setIsSendingTestPush(true);
        try {
          const result = await pushAPI.sendTestPush();
          const count = result.device_count ?? 0;
          setTestPushMessage(
            count > 0
              ? `Sent test notification to ${count} device${count === 1 ? "" : "s"}.`
              : "No subscribed devices found for test push.",
          );
        } catch (err) {
          setTestPushMessage(
            err instanceof Error ? err.message : "Failed to send test push.",
          );
        } finally {
          setIsSendingTestPush(false);
        }
      },
    },
  ];

  return (
    <>
      <SettingsPage 
        heading="Push Subscriptions" 
        actionButtons={actionButtons}
        bottomLink={{ label: "Back to Notification Settings", url: "/me/settings/notifications" }}
      >
        <Show when={testPushMessage()}>
          <div class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {testPushMessage()}
          </div>
        </Show>
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

