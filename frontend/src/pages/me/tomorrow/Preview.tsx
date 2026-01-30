import { Component, Show, createMemo } from "solid-js";
import { useNavigate } from "@solidjs/router";
import { Icon } from "@/components/shared/Icon";
import {
  faBell,
  faBullseye,
  faCalendarDay,
  faLeaf,
  faPlus,
} from "@fortawesome/free-solid-svg-icons";
import EventList from "@/components/events/List";
import ReadOnlyReminderList from "@/components/reminders/ReadOnlyList";
import ReadOnlyAlarmList from "@/components/alarms/ReadOnlyList";
import ReadOnlyRoutineGroupsChronologicalList from "@/components/routines/ReadOnlyRoutineGroupsChronologicalList";
import { useTomorrowData } from "@/pages/me/tomorrow/useTomorrowData";
import { tomorrowAPI } from "@/utils/api";

export const TomorrowPreviewPage: Component = () => {
  const navigate = useNavigate();
  const { events, tasks, routines, reminders, alarms } = useTomorrowData();

  const allTasks = createMemo(() => tasks());

  const handleRemoveAlarm = async (alarm: import("@/types/api").Alarm) => {
    // remove endpoint requires name + time, optional type/url; send best-effort
    await tomorrowAPI.removeAlarm({
      name: alarm.name,
      time: alarm.time,
      alarm_type: alarm.type,
      url: alarm.url,
    });
  };

  return (
    <div class="space-y-6">
      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3 text-left">
            <Icon icon={faCalendarDay} class="w-5 h-5 fill-amber-600" />
            <p class="text-xs uppercase tracking-wide text-amber-700">
              Calendar entries
            </p>
          </div>
        </div>
        <Show
          when={events().length > 0}
          fallback={<p class="text-sm text-stone-500">No calendar entries.</p>}
        >
          <EventList events={events} />
        </Show>
      </div>

      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3 text-left">
            <Icon icon={faBullseye} class="w-5 h-5 fill-amber-600" />
            <p class="text-xs uppercase tracking-wide text-amber-700">
              Reminders
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate("/me/tomorrow/add-reminder")}
            class="inline-flex items-center justify-center w-9 h-9 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-600/80 transition hover:bg-amber-100/80 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200"
            aria-label="Add reminder"
            title="Add reminder"
          >
            <Icon icon={faPlus} class="w-4 h-4 fill-amber-600/80" />
          </button>
        </div>
        <Show
          when={reminders().length > 0}
          fallback={<p class="text-sm text-stone-500">No reminders.</p>}
        >
          <ReadOnlyReminderList reminders={reminders} />
        </Show>
      </div>

      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3 text-left">
            <Icon icon={faBell} class="w-5 h-5 fill-amber-600" />
            <p class="text-xs uppercase tracking-wide text-amber-700">Alarms</p>
          </div>
          <button
            type="button"
            onClick={() => navigate("/me/tomorrow/add-alarm")}
            class="inline-flex items-center justify-center w-9 h-9 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-600/80 transition hover:bg-amber-100/80 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200"
            aria-label="Add alarm"
            title="Add alarm"
          >
            <Icon icon={faPlus} class="w-4 h-4 fill-amber-600/80" />
          </button>
        </div>
        <Show
          when={alarms().length > 0}
          fallback={<p class="text-sm text-stone-500">No alarms.</p>}
        >
          <ReadOnlyAlarmList alarms={alarms} onRemove={handleRemoveAlarm} />
        </Show>
      </div>

      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3 text-left">
            <Icon icon={faLeaf} class="w-5 h-5 fill-amber-600" />
            <p class="text-xs uppercase tracking-wide text-amber-700">
              Routines
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate("/me/tomorrow/routines")}
            class="inline-flex items-center justify-center w-9 h-9 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-600/80 transition hover:bg-amber-100/80 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200"
            aria-label="Add routine"
            title="Add routine"
          >
            <Icon icon={faPlus} class="w-4 h-4 fill-amber-600/80" />
          </button>
        </div>
        <Show
          when={routines().length > 0}
          fallback={<p class="text-sm text-stone-500">No routines.</p>}
        >
          <ReadOnlyRoutineGroupsChronologicalList
            tasks={allTasks()}
            routines={routines()}
            expandedByDefault={false}
          />
        </Show>
      </div>
    </div>
  );
};

export default TomorrowPreviewPage;
