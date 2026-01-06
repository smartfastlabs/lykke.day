import { createSignal } from "solid-js";
import { authAPI } from "@/utils/api";

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(buffer)));
}

export default function PushNotifications() {
  const [deviceName, setDeviceName] = createSignal("");
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setError("");

    if (!deviceName()) {
      setError("DeviceName required");
      return;
    }

    if (Notification.permission === "granted") {
      navigator.serviceWorker.ready.then((registration) => {
        registration.showNotification("asdOops!", {
          body: "You're already subscribed to push notifications.",
          icon: "/icons/192.png",
          data: { url: "/me/day/tomorrow" },
        });
      });
    } else if ("serviceWorker" in navigator) {
      setIsLoading(true);
      console.log("Service Worker is supported");
      navigator.serviceWorker.ready.then((registration) => {
        registration.pushManager
          .subscribe({
            userVisibleOnly: true,
            applicationServerKey:
              "BNWaFxSOKFUzGfVP5DOYhDSS8Nf2W9ifg4_3pNsfEzDih5CfspqP7-Ncr_9jAuwkd8jaHZPHdc0zIqHE-IPDoF8",
          })
          .then(async (subscription) => {
            console.log(
              "Push subscription:",
              subscription,
              subscription.getKey("p256dh")
            );
            const response = await fetch("/api/push/subscribe", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                device_name: deviceName(),
                endpoint: subscription.endpoint,
                keys: {
                  p256dh: arrayBufferToBase64(subscription.getKey("p256dh")!),
                  auth: arrayBufferToBase64(subscription.getKey("auth")!),
                },
              }),
            });
            console.log("Push subscription response:", response);
          })
          .catch((error) => {
            console.error("Push subscription error:", error);
          });
      });
    } else {
      console.error("Service Worker is not supported in this browser.");
    }
  };

  return (
    <div class="min-h-screen bg-neutral-50 flex flex-col items-center justify-center px-6">
      <div class="w-full max-w-sm">
        <h1 class="text-2xl font-medium text-neutral-900 text-center mb-8">
          Enable Notifications
        </h1>

        <form onSubmit={handleSubmit} class="space-y-6">
          <div>
            <label for="deviceName" class="sr-only">
              Device Name
            </label>
            <input
              id="deviceName"
              type="deviceName"
              placeholder="Device Name"
              value={deviceName()}
              onInput={(e) => setDeviceName(e.currentTarget.value)}
              class="w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow"
              autocomplete="current-deviceName"
            />
          </div>

          {error() && <p class="text-sm text-red-600 text-center">{error()}</p>}

          <button
            type="submit"
            disabled={isLoading()}
            class="w-full py-3 bg-neutral-900 text-white font-medium rounded-lg hover:bg-neutral-800 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading() ? "Signing in..." : "Continue"}
          </button>
        </form>
      </div>
    </div>
  );
}
