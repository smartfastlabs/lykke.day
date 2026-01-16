import { Component, createSignal, Show } from "solid-js";
import {
  faRotate,
  faCheck,
  faExclamationTriangle,
  faDatabase,
} from "@fortawesome/free-solid-svg-icons";
import { useStreamingData } from "@/providers/streaming-data";

const CommandsPage: Component = () => {
  const [isRescheduling, setIsRescheduling] = createSignal(false);
  const [message, setMessage] = createSignal<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [isClearing, setIsClearing] = createSignal(false);
  const [clearMessage, setClearMessage] = createSignal<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const { sync } = useStreamingData();

  const handleRescheduleToday = async () => {
    if (
      !confirm(
        "This will delete all tasks and audit logs for today and create fresh tasks from your routines. Continue?"
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
        text: "Successfully rescheduled today! All tasks have been recreated from your routines.",
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

  const handleClearLocalData = async () => {
    if (
      !confirm(
        "This will clear all locally cached data and reload everything from the server. Continue?"
      )
    ) {
      return;
    }

    setIsClearing(true);
    setClearMessage(null);

    try {
      // Clear all local storage keys used by StreamingDataProvider
      localStorage.removeItem("streaming_data.day_context");
      localStorage.removeItem("streaming_data.last_timestamp");
      localStorage.removeItem("streaming_data.routines");

      // Request full sync from server
      sync();

      setClearMessage({
        type: "success",
        text: "Successfully cleared local data! All data has been reloaded from the server.",
      });
    } catch (error) {
      console.error("Error clearing local data:", error);
      setClearMessage({
        type: "error",
        text: "Failed to clear local data. Please try again.",
      });
    } finally {
      setIsClearing(false);
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

        {/* Clear Local Data Card */}
        <div class="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl shadow-xl shadow-amber-900/5 p-6 md:p-8 mb-6">
          <div class="flex items-start gap-4">
            <div class="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center">
              <svg
                viewBox={`0 0 ${faDatabase.icon[0]} ${faDatabase.icon[1]}`}
                class="w-6 h-6 fill-amber-600"
              >
                <path d={faDatabase.icon[4] as string} />
              </svg>
            </div>
            <div class="flex-1">
              <h2 class="text-xl font-semibold text-stone-800 mb-2">
                Clear Local Data
              </h2>
              <p class="text-stone-600 mb-4">
                Clear all cached local data and reload from the server. This
                will:
              </p>
              <ul class="text-stone-600 text-sm space-y-1 mb-6 ml-4">
                <li>• Remove all locally cached day context data</li>
                <li>• Clear cached routines and timestamps</li>
                <li>• Force a full reload from the server</li>
                <li>• Resolve any sync or cache issues</li>
              </ul>

              {/* Message Display */}
              <Show when={clearMessage()}>
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
                onClick={handleClearLocalData}
                disabled={isClearing()}
                class="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-medium rounded-xl shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Show when={isClearing()} fallback="Clear Local Data">
                  <span class="flex items-center gap-2">
                    <svg
                      viewBox={`0 0 ${faRotate.icon[0]} ${faRotate.icon[1]}`}
                      class="w-4 h-4 fill-white animate-spin"
                    >
                      <path d={faRotate.icon[4] as string} />
                    </svg>
                    Clearing...
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
