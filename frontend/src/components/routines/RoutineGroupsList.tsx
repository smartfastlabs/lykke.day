import {
  Component,
  For,
  Show,
  createEffect,
  createMemo,
  createSignal,
} from "solid-js";
import { Icon } from "@/components/shared/Icon";
import {
  faChevronDown,
  faChevronRight,
  faCircleCheck,
  faHeart,
  faLeaf,
  faMoon,
  faSun,
} from "@fortawesome/free-solid-svg-icons";
import { SwipeableItem } from "@/components/shared/SwipeableItem";
import TaskList from "@/components/tasks/List";
import { useStreamingData } from "@/providers/streamingData";
import { filterVisibleTasks } from "@/utils/tasks";
import type { Routine, Task, TimingStatus } from "@/types/api";
import SnoozeActionModal from "@/components/shared/SnoozeActionModal";

export interface RoutineGroup {
  routineId: string | null;
  routineDefinitionId: string;
  routineName: string;
  tasks: Task[];
  completedCount: number;
  puntedCount: number;
  pendingCount: number;
  totalCount: number;
  timing_status?: TimingStatus | null;
  next_available_time?: string | null;
}

type RoutineStatus = TimingStatus;

export const buildRoutineGroups = (
  tasks: Task[],
  routines: Routine[],
): RoutineGroup[] => {
  const tasksByDefinition = new Map<string, Task[]>();
  tasks.forEach((task) => {
    if (!task.routine_definition_id) return;
    if (!tasksByDefinition.has(task.routine_definition_id)) {
      tasksByDefinition.set(task.routine_definition_id, []);
    }
    tasksByDefinition.get(task.routine_definition_id)!.push(task);
  });

  const groups: RoutineGroup[] = [];
  routines.forEach((routine) => {
    const routineTasks =
      tasksByDefinition.get(routine.routine_definition_id) ?? [];
    tasksByDefinition.delete(routine.routine_definition_id);
    const completedCount = routineTasks.filter(
      (t) => t.status === "COMPLETE",
    ).length;
    const puntedCount = routineTasks.filter((t) => t.status === "PUNT").length;
    const pendingCount = routineTasks.filter(
      (t) => t.status !== "COMPLETE" && t.status !== "PUNT",
    ).length;
    groups.push({
      routineId: routine.id ?? null,
      routineDefinitionId: routine.routine_definition_id,
      routineName: routine.name ?? "Routine",
      tasks: routineTasks,
      completedCount,
      puntedCount,
      pendingCount,
      totalCount: routineTasks.length,
      timing_status: routine.timing_status ?? null,
      next_available_time: routine.next_available_time ?? null,
    });
  });

  tasksByDefinition.forEach((routineTasks, routineDefinitionId) => {
    const completedCount = routineTasks.filter(
      (t) => t.status === "COMPLETE",
    ).length;
    const puntedCount = routineTasks.filter((t) => t.status === "PUNT").length;
    const pendingCount = routineTasks.filter(
      (t) => t.status !== "COMPLETE" && t.status !== "PUNT",
    ).length;
    groups.push({
      routineId: null,
      routineDefinitionId,
      routineName: "Routine",
      tasks: routineTasks,
      completedCount,
      puntedCount,
      pendingCount,
      totalCount: routineTasks.length,
      timing_status: null,
      next_available_time: null,
    });
  });

  // NOTE:
  // We intentionally return *all* routine groups here (including completed,
  // punted, and "nothing available right now" routines). Filtering is a
  // presentation concern and varies by page (e.g. `/me` summary vs
  // `/me/today/routines`).
  return groups;
};

interface RoutineGroupsListProps {
  tasks: Task[];
  routines: Routine[];
  expandedByDefault?: boolean;
  isCollapsable?: boolean;
  filterHiddenTasks?: boolean;
  filterByAvailability?: boolean;
  filterByPending?: boolean;
  collapseOutsideWindow?: boolean;
}

const getRoutineIcon = (name: string) => {
  const lowerName = name.toLowerCase();
  if (lowerName.includes("morning")) return faSun;
  if (lowerName.includes("evening") || lowerName.includes("night"))
    return faMoon;
  if (lowerName.includes("wellness") || lowerName.includes("health"))
    return faHeart;
  return faLeaf;
};

export const RoutineGroupsList: Component<RoutineGroupsListProps> = (props) => {
  const { setRoutineAction } = useStreamingData();
  const isCollapsable = () => props.isCollapsable ?? true;
  const shouldFilterHiddenTasks = () => props.filterHiddenTasks ?? true;
  const shouldFilterByAvailability = () => props.filterByAvailability ?? false;
  const shouldFilterByPending = () => props.filterByPending ?? true;
  const shouldCollapseOutsideWindow = () =>
    props.collapseOutsideWindow ?? false;
  const [expandedRoutines, setExpandedRoutines] = createSignal<Set<string>>(
    new Set(),
  );
  const [pendingRoutine, setPendingRoutine] = createSignal<RoutineGroup | null>(
    null,
  );
  const tasksForGrouping = createMemo(() =>
    shouldFilterHiddenTasks() ? filterVisibleTasks(props.tasks) : props.tasks,
  );
  const routineGroups = createMemo(() =>
    buildRoutineGroups(tasksForGrouping(), props.routines),
  );

  const handleCloseModal = () => setPendingRoutine(null);
  const handlePuntRoutine = async () => {
    const routine = pendingRoutine();
    if (!routine?.routineId) return;
    handleCloseModal();
    await setRoutineAction(routine.routineId, routine.routineDefinitionId, {
      type: "PUNT",
    });
  };
  const handleSnoozeRoutine = async (minutes: number) => {
    const routine = pendingRoutine();
    if (!routine?.routineId) return;
    handleCloseModal();
    const snoozedUntil = new Date(
      Date.now() + minutes * 60 * 1000,
    ).toISOString();
    await setRoutineAction(routine.routineId, routine.routineDefinitionId, {
      type: "SNOOZE",
      data: { snoozed_until: snoozedUntil },
    });
  };

  const getRoutineStatus = (routine: RoutineGroup): RoutineStatus =>
    routine.timing_status ?? "hidden";

  const getRoutineNextAvailableTime = (routine: RoutineGroup): Date | null => {
    if (!routine.next_available_time) return null;
    const parsed = new Date(routine.next_available_time);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  };

  const visibleRoutineGroups = createMemo(() => {
    let groups = routineGroups();
    if (shouldFilterByPending()) {
      groups = groups.filter((routine) => routine.pendingCount > 0);
    }
    if (shouldFilterByAvailability()) {
      groups = groups.filter(
        (routine) => getRoutineStatus(routine) !== "hidden",
      );
    }
    return groups;
  });

  const routineDefinitionIds = createMemo(() =>
    visibleRoutineGroups().map((group) => group.routineDefinitionId),
  );

  const routineDefinitionIdsInWindow = createMemo(() => {
    if (!shouldCollapseOutsideWindow()) return routineDefinitionIds();
    return visibleRoutineGroups()
      .filter((group) => getRoutineStatus(group) === "active")
      .map((group) => group.routineDefinitionId);
  });

  createEffect(() => {
    if (!isCollapsable() || props.expandedByDefault) {
      const ids = routineDefinitionIds();
      if (ids.length === 0) return;
      setExpandedRoutines(new Set(ids));
      return;
    }
    if (expandedRoutines().size > 0) return;
    const ids = routineDefinitionIdsInWindow();
    if (ids.length === 0) return;
    setExpandedRoutines(new Set(ids));
  });

  const toggleRoutineExpanded = (routineDefinitionId: string) => {
    setExpandedRoutines((prev) => {
      const next = new Set(prev);
      if (next.has(routineDefinitionId)) {
        next.delete(routineDefinitionId);
      } else {
        next.add(routineDefinitionId);
      }
      return next;
    });
  };

  const isRoutineExpanded = (routineDefinitionId: string) =>
    !isCollapsable() || expandedRoutines().has(routineDefinitionId);

  return (
    <div class="space-y-2.5">
      <Show when={visibleRoutineGroups().length === 0}>
        <div class="text-sm text-stone-500">
          {routineGroups().length === 0
            ? "No routines for today yet."
            : "Nothing coming up right now."}
        </div>
      </Show>
      <For each={visibleRoutineGroups()}>
        {(routine) => {
          const completionPercentage = () =>
            routine.totalCount > 0
              ? Math.round((routine.completedCount / routine.totalCount) * 100)
              : 0;

          const puntedPercentage = () =>
            routine.totalCount > 0
              ? Math.round((routine.puntedCount / routine.totalCount) * 100)
              : 0;

          const pendingPercentage = () =>
            routine.totalCount > 0
              ? Math.max(0, 100 - completionPercentage() - puntedPercentage())
              : 0;

          const isComplete = () =>
            routine.totalCount > 0 &&
            routine.completedCount === routine.totalCount;
          const isPunted = () =>
            routine.puntedCount === routine.totalCount &&
            routine.puntedCount > 0;
          const isExpanded = () =>
            isRoutineExpanded(routine.routineDefinitionId);
          const statusInfo = createMemo(() => ({
            status: getRoutineStatus(routine),
            nextAvailableTime: getRoutineNextAvailableTime(routine),
          }));

          const getStatusLabel = () => {
            const status = statusInfo().status;
            if (status === "active") return "Active";
            if (status === "available") return "Available";
            if (status === "past-due") return "Past due";
            if (status === "inactive") {
              const nextTime = statusInfo().nextAvailableTime;
              if (nextTime) {
                return `Starts ${nextTime.toLocaleTimeString([], {
                  hour: "numeric",
                  minute: "2-digit",
                })}`;
              }
              return "Soon";
            }
            const nextTime = statusInfo().nextAvailableTime;
            if (nextTime) {
              return `Starts ${nextTime.toLocaleTimeString([], {
                hour: "numeric",
                minute: "2-digit",
              })}`;
            }
            return "Later";
          };

          const getStatusPillClass = () => {
            const status = statusInfo().status;
            if (status === "active")
              return "bg-emerald-100/70 text-emerald-700";
            if (status === "available") return "bg-amber-100/80 text-amber-700";
            if (status === "past-due") return "bg-rose-100/80 text-rose-700";
            if (status === "inactive") return "bg-stone-100 text-stone-600";
            return "bg-stone-100 text-stone-600";
          };

          const getStatusClass = () => {
            if (isComplete())
              return "bg-gradient-to-br from-green-50 to-emerald-50";
            if (isPunted()) return "bg-gradient-to-br from-red-50 to-rose-50";
            if (statusInfo().status === "past-due") {
              return "bg-rose-50/70 border border-rose-100/70";
            }
            if (statusInfo().status === "active") {
              return "bg-emerald-50/70 border border-emerald-100/70";
            }
            if (statusInfo().status === "inactive") {
              return "bg-stone-50/70";
            }
            return "bg-amber-50/60 border border-amber-50/60";
          };

          const getSwipeableStatusClass = () => {
            if (isComplete())
              return "!bg-gradient-to-br !from-green-50 !to-emerald-50";
            if (isPunted())
              return "!bg-gradient-to-br !from-red-50 !to-rose-50";
            if (statusInfo().status === "past-due") {
              return "!bg-rose-50/70 !border !border-rose-100/70";
            }
            if (statusInfo().status === "active") {
              return "!bg-emerald-50/70 !border !border-emerald-100/70";
            }
            if (statusInfo().status === "inactive") {
              return "!bg-stone-50/70";
            }
            return "!bg-amber-50/60 !border !border-amber-50/60";
          };

          return (
            <div
              class={`rounded-xl p-3 transition-all duration-300 ${getStatusClass()}`}
            >
              <div class="-mx-3 -mt-3 mb-1">
                <SwipeableItem
                  onSwipeRight={() => {
                    if (!routine.routineId) return;
                    setRoutineAction(
                      routine.routineId,
                      routine.routineDefinitionId,
                      { type: "COMPLETE" },
                    );
                  }}
                  onSwipeLeft={() => {
                    if (!routine.routineId) return;
                    setPendingRoutine(routine);
                  }}
                  rightLabel="✅ Complete All Tasks"
                  leftLabel="⏸ Punt or Snooze"
                  statusClass={getSwipeableStatusClass()}
                >
                  <div
                    class="w-full flex items-start justify-between mb-2 text-left"
                    onClick={() => {
                      if (!isCollapsable()) return;
                      toggleRoutineExpanded(routine.routineDefinitionId);
                    }}
                  >
                    <div class="flex items-center gap-2">
                      <Show when={isCollapsable()}>
                        <Icon
                          icon={isExpanded() ? faChevronDown : faChevronRight}
                          class={`w-3 h-3 transition-transform duration-200 ${isComplete() ? "fill-green-600" : isPunted() ? "fill-red-600" : "fill-amber-700"}`}
                        />
                      </Show>
                      <Icon
                        icon={getRoutineIcon(routine.routineName)}
                        class={`w-4 h-4 ${isComplete() ? "fill-green-600" : isPunted() ? "fill-red-600" : "fill-amber-700"}`}
                      />
                      <span
                        class="text-sm font-semibold"
                        classList={{
                          "text-green-700": isComplete(),
                          "text-red-700": isPunted(),
                          "text-stone-800": !isComplete() && !isPunted(),
                        }}
                      >
                        {routine.routineName}
                      </span>
                    </div>
                    <div class="flex items-center gap-2">
                      <span
                        class={`rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${getStatusPillClass()}`}
                      >
                        {getStatusLabel()}
                      </span>
                      <span
                        class="text-xs font-semibold"
                        classList={{
                          "text-green-600": isComplete(),
                          "text-red-600": isPunted(),
                          "text-amber-700": !isComplete() && !isPunted(),
                        }}
                      >
                        {routine.completedCount}/{routine.totalCount}
                      </span>
                      <Show when={isComplete()}>
                        <Icon
                          icon={faCircleCheck}
                          class="w-4 h-4 fill-green-600"
                        />
                      </Show>
                    </div>
                  </div>
                </SwipeableItem>
              </div>

              <Show
                when={
                  routine.totalCount > 0 &&
                  (routine.completedCount > 0 || routine.puntedCount > 0)
                }
              >
                <div class="relative w-full h-1.5 bg-white/80 rounded-full overflow-hidden mb-3">
                  <div class="flex h-full w-full">
                    <Show when={completionPercentage() > 0}>
                      <div
                        class="h-full bg-gradient-to-r from-green-400 to-emerald-500 transition-all duration-500 ease-out"
                        style={{ width: `${completionPercentage()}%` }}
                      />
                    </Show>
                    <Show when={puntedPercentage() > 0}>
                      <div
                        class="h-full bg-gradient-to-r from-red-400 to-rose-500 transition-all duration-500 ease-out"
                        style={{ width: `${puntedPercentage()}%` }}
                      />
                    </Show>
                    <Show when={pendingPercentage() > 0}>
                      <div
                        class="h-full bg-white border-l border-white/70 transition-all duration-500 ease-out"
                        style={{ width: `${pendingPercentage()}%` }}
                      />
                    </Show>
                  </div>
                </div>
              </Show>

              <Show when={isExpanded()}>
                <div class="space-y-1.5 mt-3 transition-opacity duration-300 ease-in-out">
                  <TaskList tasks={() => routine.tasks} />
                </div>
              </Show>
            </div>
          );
        }}
      </For>
      <SnoozeActionModal
        isOpen={Boolean(pendingRoutine())}
        title="Punt or Snooze"
        onClose={handleCloseModal}
        onPunt={() => void handlePuntRoutine()}
        onSnooze={(minutes) => void handleSnoozeRoutine(minutes)}
      />
    </div>
  );
};

export default RoutineGroupsList;
