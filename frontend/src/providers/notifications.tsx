import { createSignal, For, type ParentProps } from "solid-js";

export type NotificationType = "error" | "success" | "warning" | "info";

export interface Notification {
  id: string;
  message: string;
  type: NotificationType;
  timestamp: number;
  persistent: boolean;
}

interface NotificationOptions {
  duration?: number;
  persistent?: boolean;
}

// Global signal for notifications
const [notifications, setNotifications] = createSignal<Notification[]>([]);

// Global notification functions - can be imported and used anywhere
export const globalNotifications = {
  add: (
    message: string,
    type: NotificationType = "error",
    options: NotificationOptions = {}
  ): string => {
    const { duration = 5000, persistent = false } = options;
    const id = crypto.randomUUID();

    const notification: Notification = {
      id,
      message,
      type,
      timestamp: Date.now(),
      persistent,
    };

    setNotifications((prev) => [...prev, notification]);

    if (duration > 0 && !persistent) {
      setTimeout(() => {
        globalNotifications.remove(id);
      }, duration);
    }

    return id;
  },

  remove: (id: string): void => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  },

  clear: (): void => {
    setNotifications([]);
  },

  addError: (message: string, options?: NotificationOptions): string =>
    globalNotifications.add(message, "error", options),
  
  addSuccess: (message: string, options?: NotificationOptions): string =>
    globalNotifications.add(message, "success", options),
  
  addWarning: (message: string, options?: NotificationOptions): string =>
    globalNotifications.add(message, "warning", options),
  
  addInfo: (message: string, options?: NotificationOptions): string =>
    globalNotifications.add(message, "info", options),
};

// Simple provider that just renders children (keeps app structure consistent)
export function NotificationProvider(props: ParentProps) {
  return <>{props.children}</>;
}

// Notification UI container - renders the toast notifications
export function NotificationContainer() {
  return (
    <div class="fixed top-4 right-4 z-50 space-y-2">
      <For each={notifications()}>
        {(notification) => (
          <div
            class={`p-4 rounded-lg shadow-lg max-w-sm transition-all duration-300 ${
              notification.type === "error"
                ? "bg-red-500 text-white"
                : notification.type === "success"
                ? "bg-green-500 text-white"
                : notification.type === "warning"
                ? "bg-yellow-500 text-black"
                : "bg-blue-500 text-white"
            }`}
          >
            <div class="flex items-center justify-between">
              <p class="flex-1">{notification.message}</p>
              <button
                onClick={() => globalNotifications.remove(notification.id)}
                class="ml-4 text-lg font-bold opacity-70 hover:opacity-100"
              >
                ×
              </button>
            </div>
          </div>
        )}
      </For>
    </div>
  );
}
