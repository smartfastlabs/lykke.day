import { Component } from "solid-js";
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
    <div class="flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-md space-y-6">
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Calendar Details</h2>
          <div class="space-y-3">
            <div>
              <label class="text-sm font-medium text-neutral-500">Name</label>
              <div class="mt-1 text-base text-neutral-900">
                {props.calendar.name}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">
                Platform
              </label>
              <div class="mt-1 text-base text-neutral-900">
                {props.calendar.platform}
                {props.calendar.platform_id
                  ? ` • ${props.calendar.platform_id}`
                  : ""}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">
                Auth Token ID
              </label>
              <div class="mt-1 text-xs text-neutral-900 break-all">
                {props.calendar.auth_token_id}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">
                Default Event Category
              </label>
              <div class="mt-1 text-base text-neutral-900">
                {props.calendar.default_event_category ?? "Not set"}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">
                Last Sync
              </label>
              <div class="mt-1 text-base text-neutral-900">
                {formatDateTime(props.calendar.last_sync_at)}
              </div>
            </div>
            <div class="flex items-center justify-between">
              <div>
                <label class="text-sm font-medium text-neutral-500">
                  Sync Status
                </label>
                <div class="mt-1 text-base text-neutral-900 flex items-center gap-2">
                  <span
                    class={`text-xs px-2 py-1 rounded-full ${
                      isSynced()
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {isSynced() ? "Enabled" : "Disabled"}
                  </span>
                  <span class="text-xs text-neutral-500">
                    {isSynced()
                      ? `Expires ${syncExpiration()}`
                      : "Not receiving updates"}
                  </span>
                </div>
              </div>
              <div class="flex items-center gap-2">
                {props.onResync && (
                  <button
                    type="button"
                    class={`rounded-md border border-neutral-200 px-3 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50 ${
                      props.isResyncing ? "opacity-70 cursor-not-allowed" : ""
                    }`}
                    onClick={() => props.onResync?.()}
                    disabled={props.isResyncing || props.isToggling}
                  >
                    {props.isResyncing ? "Resyncing..." : "Resync"}
                  </button>
                )}
                {props.onToggleSync && (
                  <button
                    type="button"
                    class={`rounded-md px-3 py-2 text-sm font-medium ${
                      isSynced()
                        ? "border border-red-200 text-red-700 hover:bg-red-50"
                        : "bg-emerald-600 text-white hover:bg-emerald-700"
                    } ${
                      props.isToggling || props.isResyncing
                        ? "opacity-70 cursor-not-allowed"
                        : ""
                    }`}
                    onClick={() => props.onToggleSync?.()}
                    disabled={props.isToggling || props.isResyncing}
                  >
                    {props.isToggling
                      ? "Working..."
                      : isSynced()
                        ? "Disable Sync"
                        : "Enable Sync"}
                  </button>
                )}
              </div>
            </div>
            {props.calendar.platform === "google" && props.calendar.auth_token_id && (
              <div class="pt-2 border-t border-neutral-200">
                <a
                  href={`/api/google/login?auth_token_id=${props.calendar.auth_token_id}`}
                  class="inline-flex items-center justify-center rounded-md border border-neutral-300 bg-white px-4 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-neutral-500 focus:ring-offset-2"
                >
                  Re-authenticate Google Calendar
                </a>
                <p class="mt-2 text-xs text-neutral-500">
                  If your calendar sync is not working, you may need to re-authenticate your Google account.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CalendarPreview;
