import { createMemo, Show } from "solid-js";
import { getTime } from "../../utils/dates";
import TimeBadge from "../shared/timeBadge";

function TaskRow(task) {
  const startTime = createMemo(() => {
    const v = task.schedule.start_time || task.schedule.end_time;
    if (v) {
      return getTime(task.date, v);
    }
  });

  return (
    <div class="group flex items-center justify-between gap-4 px-4 py-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors">
      <div class="flex flex-col min-w-0">
        <h3 class="text-gray-900 font-medium truncate">{task.name}</h3>
        <span class="text-xs text-gray-400 tracking-wide uppercase">
          {task.task_definition.type}
        </span>
      </div>
      <Show when={startTime()}>
        <div class="flex flex-col min-w-5">
          <TimeBadge value={startTime()} />
        </div>
      </Show>
    </div>
  );
}

export default TaskRow;
