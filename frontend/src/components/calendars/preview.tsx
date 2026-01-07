import { Component } from "solid-js";
import { Calendar } from "@/types/api";

interface CalendarPreviewProps {
  calendar: Calendar;
}

const formatDateTime = (value?: string | null): string => {
  if (!value) return "Not synced yet";
  const date = new Date(value);
  return isNaN(date.getTime()) ? value : date.toLocaleString();
};

const CalendarPreview: Component<CalendarPreviewProps> = (props) => {
  return (
    <div class="flex flex-col items-center justify-center px-6 py-8">
      <div class="w-full max-w-md space-y-6">
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-medium text-neutral-900">Calendar Details</h2>
          <div class="space-y-3">
            <div>
              <label class="text-sm font-medium text-neutral-500">Name</label>
              <div class="mt-1 text-base text-neutral-900">{props.calendar.name}</div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Platform</label>
              <div class="mt-1 text-base text-neutral-900">
                {props.calendar.platform}
                {props.calendar.platform_id ? ` • ${props.calendar.platform_id}` : ""}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Auth Token ID</label>
              <div class="mt-1 text-xs text-neutral-900 break-all">
                {props.calendar.auth_token_id}
              </div>
            </div>
            <div>
              <label class="text-sm font-medium text-neutral-500">Last Sync</label>
              <div class="mt-1 text-base text-neutral-900">
                {formatDateTime(props.calendar.last_sync_at)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CalendarPreview;

