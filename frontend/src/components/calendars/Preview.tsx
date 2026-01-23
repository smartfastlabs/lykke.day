import { Component, Show } from "solid-js";
import type { CalendarWithCategory } from "./Form";

interface CalendarPreviewProps {
  calendar: CalendarWithCategory;
  onToggleSync?: () => Promise<void> | void;
  isToggling?: boolean;
  onResync?: () => Promise<void> | void;
  isResyncing?: boolean;
}

const formatDateTime = (value?: string | null): string => {
  if (!value) return "Not synced yet";
  const date = new Date(value);
  return isNaN(date.getTime()) ? value : date.toLocaleString();
};

const CalendarPreview: Component<CalendarPreviewProps> = (props) => {
  const isSynced = () =>
    props.calendar.sync_enabled ?? Boolean(props.calendar.sync_subscription);

  const syncExpiration = () => {
    const expiration = props.calendar.sync_subscription?.expiration;
    return expiration ? formatDateTime(expiration) : "No active subscription";
  };

  return (
    <div class="w-full px-6 py-8">
      <div class="max-w-2xl mx-auto space-y-6">
        {/* Hero Section */}
        <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100/50">
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <h2 class="text-2xl font-bold text-gray-900 mb-2">
                {props.calendar.name}
              </h2>
              <div class="flex items-center gap-2 text-sm text-gray-600">
                <span class="font-medium capitalize">{props.calendar.platform}</span>
                <Show when={props.calendar.platform_id}>
                  <span class="text-gray-400">•</span>
                  <span class="text-gray-500 font-mono text-xs truncate max-w-md">
                    {props.calendar.platform_id}
                  </span>
                </Show>
              </div>
            </div>
            <div
              class={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium shadow-sm ${
                isSynced()
                  ? "bg-emerald-500/10 text-emerald-700 border border-emerald-200/50"
                  : "bg-gray-100 text-gray-600 border border-gray-200"
              }`}
            >
              <div
                class={`w-2 h-2 rounded-full ${
                  isSynced() ? "bg-emerald-500 animate-pulse" : "bg-gray-400"
                }`}
              />
              {isSynced() ? "Sync Enabled" : "Sync Disabled"}
            </div>
          </div>
        </div>

        {/* Details Grid */}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-white rounded-xl border border-gray-200 p-5 hover:border-gray-300 transition-colors">
            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">
              Default Event Category
            </label>
            <div class="text-base font-medium text-gray-900">
              {props.calendar.default_event_category ?? (
                <span class="text-gray-400 italic">Not set</span>
              )}
            </div>
          </div>

          <div class="bg-white rounded-xl border border-gray-200 p-5 hover:border-gray-300 transition-colors">
            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">
              Last Sync
            </label>
            <div class="text-base font-medium text-gray-900">
              {formatDateTime(props.calendar.last_sync_at)}
            </div>
          </div>
        </div>

        {/* Sync Control Section */}
        <div class="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-semibold text-gray-900 mb-1">
                Sync Status
              </h3>
              <p class="text-sm text-gray-500">
                {isSynced() ? (
                  <>
                    Active subscription
                    <Show when={props.calendar.sync_subscription?.expiration}>
                      <span class="ml-1">
                        • Expires {syncExpiration()}
                      </span>
                    </Show>
                  </>
                ) : (
                  "Not receiving updates"
                )}
              </p>
            </div>
            <div class="flex items-center gap-3">
              <Show when={props.onResync}>
                <button
                  type="button"
                  class={`inline-flex items-center justify-center rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 hover:border-gray-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:border-gray-300 ${
                    props.isResyncing ? "opacity-70 cursor-not-allowed" : ""
                  }`}
                  onClick={() => props.onResync?.()}
                  disabled={props.isResyncing || props.isToggling}
                >
                  <Show
                    when={!props.isResyncing}
                    fallback={
                      <>
                        <svg
                          class="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-600"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            class="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            stroke-width="4"
                          />
                          <path
                            class="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Resyncing...
                      </>
                    }
                  >
                    <svg
                      class="-ml-1 mr-2 h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                    Resync
                  </Show>
                </button>
              </Show>
              <Show when={props.onToggleSync}>
                <button
                  type="button"
                  class={`inline-flex items-center justify-center rounded-lg px-5 py-2.5 text-sm font-medium shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                    isSynced()
                      ? "border border-red-300 bg-white text-red-600 hover:bg-red-50 hover:border-red-400"
                      : "bg-emerald-600 text-white hover:bg-emerald-700 shadow-emerald-500/50"
                  } ${
                    props.isToggling || props.isResyncing
                      ? "opacity-70 cursor-not-allowed"
                      : ""
                  }`}
                  onClick={() => props.onToggleSync?.()}
                  disabled={props.isToggling || props.isResyncing}
                >
                  <Show
                    when={!props.isToggling}
                    fallback={
                      <>
                        <svg
                          class="animate-spin -ml-1 mr-2 h-4 w-4"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            class="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            stroke-width="4"
                          />
                          <path
                            class="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Working...
                      </>
                    }
                  >
                    {isSynced() ? "Disable Sync" : "Enable Sync"}
                  </Show>
                </button>
              </Show>
            </div>
          </div>
        </div>

        {/* Technical Details */}
        <Show when={props.calendar.auth_token_id}>
          <div class="bg-gray-50 rounded-xl border border-gray-200 p-5">
            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">
              Auth Token ID
            </label>
            <div class="text-xs font-mono text-gray-700 break-all bg-white px-3 py-2 rounded-md border border-gray-200">
              {props.calendar.auth_token_id}
            </div>
          </div>
        </Show>

        {/* Google Re-authentication */}
        <Show
          when={props.calendar.platform === "google" && props.calendar.auth_token_id}
        >
          <div class="bg-amber-50/50 border border-amber-200/50 rounded-xl p-6">
            <div class="flex items-start gap-4">
              <div class="flex-shrink-0">
                <svg
                  class="w-5 h-5 text-amber-600 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <div class="flex-1">
                <h4 class="text-sm font-semibold text-gray-900 mb-1">
                  Need to Re-authenticate?
                </h4>
                <p class="text-sm text-gray-600 mb-4">
                  If your calendar sync is not working, you may need to
                  re-authenticate your Google account.
                </p>
                <a
                  href={`/api/google/login?auth_token_id=${props.calendar.auth_token_id}`}
                  onClick={(event) => {
                    event.preventDefault();
                    window.location.assign(
                      `/api/google/login?auth_token_id=${props.calendar.auth_token_id}`
                    );
                  }}
                  class="inline-flex items-center justify-center rounded-lg border border-amber-300 bg-white px-4 py-2.5 text-sm font-medium text-amber-700 shadow-sm hover:bg-amber-50 hover:border-amber-400 transition-all"
                >
                  Re-authenticate Google Calendar
                  <svg
                    class="ml-2 h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </a>
              </div>
            </div>
          </div>
        </Show>
      </div>
    </div>
  );
};

export default CalendarPreview;
