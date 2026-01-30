import { Component, createSignal, Show } from "solid-js";
import {
  faRotate,
  faCheck,
  faExclamationTriangle,
  faCalendar,
  faBell,
} from "@fortawesome/free-solid-svg-icons";

const CommandsPage: Component = () => {
  const [isRescheduling, setIsRescheduling] = createSignal(false);
  const [message, setMessage] = createSignal<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [isResettingSync, setIsResettingSync] = createSignal(false);
  const [resetSyncMessage, setResetSyncMessage] = createSignal<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [isSendingTestPush, setIsSendingTestPush] = createSignal(false);
  const [testPushMessage, setTestPushMessage] = createSignal<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const handleRescheduleToday = async () => {
    if (
      !confirm(
        "This will delete all tasks and audit logs for today and create fresh tasks from your routine definitions. Continue?",
      )
    ) {
      return;
    }

    setIsRescheduling(true);
    setMessage(null);

    try {
      const response = await fetch("/api/days/today/reschedule", {
        method: "PUT",
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Failed to reschedule today");
      }

      setMessage({
        type: "success",
        text: "Successfully rescheduled today! All tasks have been recreated from your routine definitions.",
      });

      // Reload the page after a short delay to show the updated tasks
      setTimeout(() => {
        window.location.href = "/me/today";
      }, 2000);
    } catch (error) {
      console.error("Error rescheduling today:", error);
      setMessage({
        type: "error",
        text: "Failed to reschedule today. Please try again.",
      });
    } finally {
      setIsRescheduling(false);
    }
  };

  const handleResetCalendarSync = async () => {
    if (
      !confirm(
        "This will unsubscribe all calendars from syncing, delete all future calendar events, then resubscribe and resync. Continue?",
      )
    ) {
      return;
    }

    setIsResettingSync(true);
    setResetSyncMessage(null);

    try {
      const response = await fetch("/api/calendars/reset-sync", {
        method: "POST",
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Failed to reset calendar sync");
      }

      setResetSyncMessage({
        type: "success",
        text: "Successfully reset calendar sync! All calendars have been unsubscribed, future events deleted, and resynced.",
      });
    } catch (error) {
      console.error("Error resetting calendar sync:", error);
      setResetSyncMessage({
        type: "error",
        text: "Failed to reset calendar sync. Please try again.",
      });
    } finally {
      setIsResettingSync(false);
    }
  };

  const handleSendTestPush = async () => {
    setIsSendingTestPush(true);
    setTestPushMessage(null);

    try {
      // Send push notification
      const [pushResponse] = await Promise.allSettled([
        fetch("/api/push/test-push/", {
          method: "POST",
          credentials: "include",
        }),
      ]);

      const pushSuccess =
        pushResponse.status === "fulfilled" && pushResponse.value.ok;

      if (!pushSuccess) {
        throw new Error("Failed to send test notifications");
      }

      let messageText = "";
      const parts: string[] = [];

      if (pushSuccess) {
        try {
          const pushData = await pushResponse.value.json();
          const deviceCount = pushData.device_count || 0;
          if (deviceCount > 0) {
            parts.push(
              `push notification to ${deviceCount} device${deviceCount === 1 ? "" : "s"}`,
            );
          } else {
            parts.push("push notification (no devices subscribed)");
          }
        } catch {
          parts.push("push notification");
        }
      }

      if (parts.length === 0) {
        setTestPushMessage({
          type: "error",
          text: "Failed to send test notifications. Please try again.",
        });
      } else {
        messageText = `Test ${parts.join(" and ")} sent!`;
        setTestPushMessage({
          type: "success",
          text: messageText,
        });
      }
    } catch (error) {
      console.error("Error sending test notifications:", error);
      setTestPushMessage({
        type: "error",
        text: "Failed to send test notifications. Please try again.",
      });
    } finally {
      setIsSendingTestPush(false);
    }
  };

  return (
    <div class="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50">
      <div class="max-w-4xl mx-auto px-6 py-12">
        <div class="mb-8">
          <h1 class="text-3xl md:text-4xl font-bold text-stone-800 mb-2">
            Commands
          </h1>
          <p class="text-stone-600">
            Perform maintenance and cleanup operations
          </p>
        </div>

        {/* Reschedule Today Card */}
        <div class="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl shadow-xl shadow-amber-900/5 p-6 md:p-8 mb-6">
          <div class="flex items-start gap-4">
            <div class="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center">
              <svg
                viewBox={`0 0 ${faRotate.icon[0]} ${faRotate.icon[1]}`}
                class="w-6 h-6 fill-amber-600"
              >
                <path d={faRotate.icon[4] as string} />
              </svg>
            </div>
            <div class="flex-1">
              <h2 class="text-xl font-semibold text-stone-800 mb-2">
                Reschedule Today
              </h2>
              <p class="text-stone-600 mb-4">
                Clean up and recreate all tasks for today. This will:
              </p>
              <ul class="text-stone-600 text-sm space-y-1 mb-6 ml-4">
                <li>• Delete all existing tasks for today</li>
                <li>• Remove all audit logs for today</li>
                <li>• Create fresh tasks from your current routines</li>
                <li>• Fix any duplicate or sync issues</li>
              </ul>

              {/* Message Display */}
              <Show when={message()}>
                {(msg) => (
                  <div
                    class="mb-4 p-4 rounded-lg flex items-center gap-3"
                    classList={{
                      "bg-green-50 border border-green-200":
                        msg().type === "success",
                      "bg-red-50 border border-red-200": msg().type === "error",
                    }}
                  >
                    <svg
                      viewBox={`0 0 ${(msg().type === "success" ? faCheck : faExclamationTriangle).icon[0]} ${(msg().type === "success" ? faCheck : faExclamationTriangle).icon[1]}`}
                      class="w-5 h-5 flex-shrink-0"
                      classList={{
                        "fill-green-600": msg().type === "success",
                        "fill-red-600": msg().type === "error",
                      }}
                    >
                      <path
                        d={
                          (msg().type === "success"
                            ? faCheck
                            : faExclamationTriangle
                          ).icon[4] as string
                        }
                      />
                    </svg>
                    <p
                      class="text-sm"
                      classList={{
                        "text-green-800": msg().type === "success",
                        "text-red-800": msg().type === "error",
                      }}
                    >
                      {msg().text}
                    </p>
                  </div>
                )}
              </Show>

              <button
                onClick={handleRescheduleToday}
                disabled={isRescheduling()}
                class="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-medium rounded-xl shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Show when={isRescheduling()} fallback="Reschedule Today">
                  <span class="flex items-center gap-2">
                    <svg
                      viewBox={`0 0 ${faRotate.icon[0]} ${faRotate.icon[1]}`}
                      class="w-4 h-4 fill-white animate-spin"
                    >
                      <path d={faRotate.icon[4] as string} />
                    </svg>
                    Rescheduling...
                  </span>
                </Show>
              </button>
            </div>
          </div>
        </div>

        {/* Reset Calendar Sync Card */}
        <div class="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl shadow-xl shadow-amber-900/5 p-6 md:p-8 mb-6">
          <div class="flex items-start gap-4">
            <div class="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center">
              <svg
                viewBox={`0 0 ${faCalendar.icon[0]} ${faCalendar.icon[1]}`}
                class="w-6 h-6 fill-amber-600"
              >
                <path d={faCalendar.icon[4] as string} />
              </svg>
            </div>
            <div class="flex-1">
              <h2 class="text-xl font-semibold text-stone-800 mb-2">
                Reset Calendar Sync
              </h2>
              <p class="text-stone-600 mb-4">
                Reset calendar synchronization for all subscribed calendars.
                This will:
              </p>
              <ul class="text-stone-600 text-sm space-y-1 mb-6 ml-4">
                <li>
                  • Unsubscribe all calendars from syncing (that have it
                  enabled)
                </li>
                <li>• Delete all future events for these calendars</li>
                <li>
                  • Resubscribe to updates for all calendars that were
                  previously subscribed
                </li>
                <li>• Perform initial sync for each calendar</li>
              </ul>

              {/* Message Display */}
              <Show when={resetSyncMessage()}>
                {(msg) => (
                  <div
                    class="mb-4 p-4 rounded-lg flex items-center gap-3"
                    classList={{
                      "bg-green-50 border border-green-200":
                        msg().type === "success",
                      "bg-red-50 border border-red-200": msg().type === "error",
                    }}
                  >
                    <svg
                      viewBox={`0 0 ${(msg().type === "success" ? faCheck : faExclamationTriangle).icon[0]} ${(msg().type === "success" ? faCheck : faExclamationTriangle).icon[1]}`}
                      class="w-5 h-5 flex-shrink-0"
                      classList={{
                        "fill-green-600": msg().type === "success",
                        "fill-red-600": msg().type === "error",
                      }}
                    >
                      <path
                        d={
                          (msg().type === "success"
                            ? faCheck
                            : faExclamationTriangle
                          ).icon[4] as string
                        }
                      />
                    </svg>
                    <p
                      class="text-sm"
                      classList={{
                        "text-green-800": msg().type === "success",
                        "text-red-800": msg().type === "error",
                      }}
                    >
                      {msg().text}
                    </p>
                  </div>
                )}
              </Show>

              <button
                onClick={handleResetCalendarSync}
                disabled={isResettingSync()}
                class="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-medium rounded-xl shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Show when={isResettingSync()} fallback="Reset Calendar Sync">
                  <span class="flex items-center gap-2">
                    <svg
                      viewBox={`0 0 ${faRotate.icon[0]} ${faRotate.icon[1]}`}
                      class="w-4 h-4 fill-white animate-spin"
                    >
                      <path d={faRotate.icon[4] as string} />
                    </svg>
                    Resetting...
                  </span>
                </Show>
              </button>
            </div>
          </div>
        </div>

        {/* Send Test Push Card */}
        <div class="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl shadow-xl shadow-amber-900/5 p-6 md:p-8 mb-6">
          <div class="flex items-start gap-4">
            <div class="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center">
              <svg
                viewBox={`0 0 ${faBell.icon[0]} ${faBell.icon[1]}`}
                class="w-6 h-6 fill-amber-600"
              >
                <path d={faBell.icon[4] as string} />
              </svg>
            </div>
            <div class="flex-1">
              <h2 class="text-xl font-semibold text-stone-800 mb-2">
                Send Test Push
              </h2>
              <p class="text-stone-600 mb-4">
                Send a test push notification to all your subscribed devices and
                kiosk displays. This helps verify that notifications are working
                correctly.
              </p>
              <ul class="text-stone-600 text-sm space-y-1 mb-6 ml-4">
                <li>• Sends to all devices with notifications enabled</li>
                <li>
                  • Sends to all connected kiosk displays (will be read aloud)
                </li>
                <li>• Verifies your push notification and kiosk setup</li>
                <li>• No data is modified</li>
              </ul>

              {/* Message Display */}
              <Show when={testPushMessage()}>
                {(msg) => (
                  <div
                    class="mb-4 p-4 rounded-lg flex items-center gap-3"
                    classList={{
                      "bg-green-50 border border-green-200":
                        msg().type === "success",
                      "bg-red-50 border border-red-200": msg().type === "error",
                    }}
                  >
                    <svg
                      viewBox={`0 0 ${(msg().type === "success" ? faCheck : faExclamationTriangle).icon[0]} ${(msg().type === "success" ? faCheck : faExclamationTriangle).icon[1]}`}
                      class="w-5 h-5 flex-shrink-0"
                      classList={{
                        "fill-green-600": msg().type === "success",
                        "fill-red-600": msg().type === "error",
                      }}
                    >
                      <path
                        d={
                          (msg().type === "success"
                            ? faCheck
                            : faExclamationTriangle
                          ).icon[4] as string
                        }
                      />
                    </svg>
                    <p
                      class="text-sm"
                      classList={{
                        "text-green-800": msg().type === "success",
                        "text-red-800": msg().type === "error",
                      }}
                    >
                      {msg().text}
                    </p>
                  </div>
                )}
              </Show>

              <button
                onClick={handleSendTestPush}
                disabled={isSendingTestPush()}
                class="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-medium rounded-xl shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Show when={isSendingTestPush()} fallback="Send Test Push">
                  <span class="flex items-center gap-2">
                    <svg
                      viewBox={`0 0 ${faRotate.icon[0]} ${faRotate.icon[1]}`}
                      class="w-4 h-4 fill-white animate-spin"
                    >
                      <path d={faRotate.icon[4] as string} />
                    </svg>
                    Sending...
                  </span>
                </Show>
              </button>
            </div>
          </div>
        </div>

        {/* Warning Card */}
        <div class="bg-amber-50/60 backdrop-blur-md border border-amber-200/80 rounded-2xl p-6">
          <div class="flex items-start gap-3">
            <svg
              viewBox={`0 0 ${faExclamationTriangle.icon[0]} ${faExclamationTriangle.icon[1]}`}
              class="w-5 h-5 fill-amber-600 mt-1 flex-shrink-0"
            >
              <path d={faExclamationTriangle.icon[4] as string} />
            </svg>
            <div>
              <h3 class="font-semibold text-amber-900 mb-1">Warning</h3>
              <p class="text-amber-800 text-sm">
                Rescheduling will permanently delete all tasks and audit logs
                for the selected date. This action cannot be undone. Make sure
                this is what you want before proceeding.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommandsPage;
