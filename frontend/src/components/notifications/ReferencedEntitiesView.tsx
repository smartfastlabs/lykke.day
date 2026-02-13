import { useNavigate } from "@solidjs/router";
import { Component, Show, createMemo } from "solid-js";
import { useStreamingData } from "@/providers/streamingData";
import { Icon } from "@/components/shared/Icon";
import { faBell, faLeaf, faListCheck } from "@fortawesome/free-solid-svg-icons";
import TaskList from "@/components/tasks/List";
import RoutineGroupsList from "@/components/routines/RoutineGroupsList";
import AlarmList from "@/components/alarms/List";
import type { Alarm, ReferencedEntity, Routine, Task } from "@/types/api";

interface Props {
  referencedEntities: ReferencedEntity[];
}

const normalizeType = (entityType: string): string =>
  entityType.toLowerCase().replace(/_/g, "");

const NotificationReferencedEntitiesView: Component<Props> = (props) => {
  const navigate = useNavigate();
  const { tasks, routines, alarms } = useStreamingData();

  const taskIds = createMemo(() => {
    const ids = new Set<string>();
    for (const ref of props.referencedEntities) {
      if (normalizeType(ref.entity_type) === "task") ids.add(ref.entity_id);
    }
    return ids;
  });

  const routineIds = createMemo(() => {
    const ids = new Set<string>();
    for (const ref of props.referencedEntities) {
      if (normalizeType(ref.entity_type) === "routine") ids.add(ref.entity_id);
    }
    return ids;
  });

  const alarmIds = createMemo(() => {
    const ids = new Set<string>();
    for (const ref of props.referencedEntities) {
      if (normalizeType(ref.entity_type) === "alarm") ids.add(ref.entity_id);
    }
    return ids;
  });

  const referencedTasks = createMemo<Task[]>(() => {
    const ids = taskIds();
    return (tasks() ?? []).filter((task) => !!task.id && ids.has(task.id));
  });

  const referencedRoutines = createMemo<Routine[]>(() => {
    const ids = routineIds();
    return (routines() ?? []).filter(
      (routine) => !!routine.id && ids.has(routine.id),
    );
  });

  const routineTaskPool = createMemo<Task[]>(() => {
    const definitionIds = new Set(
      referencedRoutines().map((routine) => routine.routine_definition_id),
    );
    return (tasks() ?? []).filter(
      (task) =>
        !!task.routine_definition_id && definitionIds.has(task.routine_definition_id),
    );
  });

  const referencedAlarms = createMemo<Alarm[]>(() => {
    const ids = alarmIds();
    return (alarms() ?? []).filter((alarm) => !!alarm.id && ids.has(alarm.id));
  });

  const unresolvedTasks = createMemo(() => taskIds().size - referencedTasks().length);
  const unresolvedRoutines = createMemo(
    () => routineIds().size - referencedRoutines().length,
  );
  const unresolvedAlarms = createMemo(
    () => alarmIds().size - referencedAlarms().length,
  );

  const hasAnySection = createMemo(
    () => taskIds().size > 0 || routineIds().size > 0 || alarmIds().size > 0,
  );

  return (
    <div class="space-y-6">
      <Show
        when={hasAnySection()}
        fallback={
          <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm text-center text-sm text-stone-500">
            No task, routine, or alarm references in this notification.
          </div>
        }
      >
        <Show when={taskIds().size > 0}>
          <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-3">
            <button
              type="button"
              onClick={() => navigate("/me/today/tasks")}
              class="flex items-center gap-3 text-left"
            >
              <Icon icon={faListCheck} class="w-5 h-5 fill-amber-600" />
              <p class="text-xs uppercase tracking-wide text-amber-700">Tasks</p>
            </button>
            <Show when={referencedTasks().length > 0}>
              <div class="space-y-1">
                <TaskList tasks={referencedTasks} />
              </div>
            </Show>
            <Show when={unresolvedTasks() > 0}>
              <p class="text-xs text-stone-500">
                {unresolvedTasks()} referenced task(s) not loaded for this day.
              </p>
            </Show>
          </div>
        </Show>

        <Show when={routineIds().size > 0}>
          <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-3">
            <button
              type="button"
              onClick={() => navigate("/me/today/routines")}
              class="flex items-center gap-3 text-left"
            >
              <Icon icon={faLeaf} class="w-5 h-5 fill-amber-600" />
              <p class="text-xs uppercase tracking-wide text-amber-700">
                Routines
              </p>
            </button>
            <Show when={referencedRoutines().length > 0}>
              <div class="space-y-1">
                <RoutineGroupsList
                  tasks={routineTaskPool()}
                  routines={referencedRoutines()}
                  filterHiddenTasks={false}
                  filterByAvailability={false}
                  filterByPending={false}
                  collapseOutsideWindow={false}
                />
              </div>
            </Show>
            <Show when={unresolvedRoutines() > 0}>
              <p class="text-xs text-stone-500">
                {unresolvedRoutines()} referenced routine(s) not loaded for this
                day.
              </p>
            </Show>
          </div>
        </Show>

        <Show when={alarmIds().size > 0}>
          <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-3">
            <button
              type="button"
              onClick={() => navigate("/me/today/alarms")}
              class="flex items-center gap-3 text-left"
            >
              <Icon icon={faBell} class="w-5 h-5 fill-amber-600" />
              <p class="text-xs uppercase tracking-wide text-amber-700">Alarms</p>
            </button>
            <Show when={referencedAlarms().length > 0}>
              <div class="space-y-1">
                <AlarmList alarms={referencedAlarms} />
              </div>
            </Show>
            <Show when={unresolvedAlarms() > 0}>
              <p class="text-xs text-stone-500">
                {unresolvedAlarms()} referenced alarm(s) not loaded for this day.
              </p>
            </Show>
          </div>
        </Show>
      </Show>
    </div>
  );
};

export default NotificationReferencedEntitiesView;
