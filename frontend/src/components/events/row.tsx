import { getTime } from "../../utils/dates";
import TimeBadge from "../shared/timeBadge";
import { createMemo } from "solid-js";

function EventRow(event) {
  const startTime = createMemo(() => {
    if (event.starts_at) {
      return getTime(event.date, event.starts_at);
    }
  });

  return (
    <div class="group flex items-center justify-between gap-4 px-4 py-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors">
      <div class="flex flex-col min-w-0">
        <h3 class="text-gray-900 font-medium truncate">{event.name}</h3>
        <span class="text-xs text-gray-400 tracking-wide uppercase">
          {event.platform}
        </span>
      </div>
      <Show when={startTime()}>
        <TimeBadge value={startTime()} />
      </Show>
    </div>
  );
}

export default EventRow;
