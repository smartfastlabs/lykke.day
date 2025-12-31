import {
  createContext,
  useContext,
  createSignal,
  For,
  type Component,
  type ParentProps,
  type Accessor,
} from "solid-js";

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

// Create a global signal that can be imported anywhere
export const [notifications, setNotifications] = createSignal<Notification[]>([]);

// Global notification functions that can be imported anywhere
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

    // Auto-remove after duration
    if (duration > 0 && !persistent) {
      setTimeout(() => {
        globalNotifications.remove(id);
      }, duration);
    }

    return id;
  },

  remove: (id: string): void => {
    setNotifications((prev) =>
      prev.filter((notification) => notification.id !== id)
    );
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

interface NotificationContextValue {
  notifications: Accessor<Notification[]>;
  add: (message: string, type?: NotificationType, options?: NotificationOptions) => string;
  remove: (id: string) => void;
  clear: () => void;
  addError: (message: string, options?: NotificationOptions) => string;
  addSuccess: (message: string, options?: NotificationOptions) => string;
  addWarning: (message: string, options?: NotificationOptions) => string;
  addInfo: (message: string, options?: NotificationOptions) => string;
}

const NotificationContext = createContext<NotificationContextValue>();

export function NotificationProvider(props: ParentProps) {
  // The provider now just wraps the global signal
  const contextValue: NotificationContextValue = {
    notifications,
    ...globalNotifications,
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {props.children}
    </NotificationContext.Provider>
  );
}

export function useNotifications(): NotificationContextValue {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error(
      "useNotifications must be used within NotificationProvider"
    );
  }
  return context;
}

export function NotificationContainer() {
  // Use the global signal directly
  const remove = globalNotifications.remove;

  return (
    <div class="notification-container fixed top-4 right-4 z-50 space-y-2">
      <For each={notifications()}>
        {(notification) => (
          <div
            class={`notification p-4 rounded-lg shadow-lg max-w-sm transition-all duration-300 ${
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
                onClick={() => remove(notification.id)}
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
