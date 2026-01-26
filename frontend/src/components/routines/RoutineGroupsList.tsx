import {
  Component,
  For,
  Show,
  createEffect,
  createMemo,
  createSignal,
  onCleanup,
  onMount,
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
import { getDateString, getTime } from "@/utils/dates";
import { filterVisibleTasks } from "@/utils/tasks";
import type { Routine, Task, TimeWindow } from "@/types/api";
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
  timeWindow?: TimeWindow | null;
}

type RoutineStatus = "hidden" | "inactive" | "available" | "active" | "past-due";
type TaskWindowStatus = {
  isActive: boolean;
  isAvailable: boolean;
  isPastDue: boolean;
  nextAvailableTime: Date | null;
};
type RoutineStatusInfo = {
  status: RoutineStatus;
  nextAvailableTime: Date | null;
};

const UPCOMING_WINDOW_MS = 1000 * 60 * 120;

export const buildRoutineGroups = (
  tasks: Task[],
  routines: Routine[]
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
    const routineTasks = tasksByDefinition.get(routine.routine_definition_id) ?? [];
    tasksByDefinition.delete(routine.routine_definition_id);
    const completedCount = routineTasks.filter((t) => t.status === "COMPLETE").length;
    const puntedCount = routineTasks.filter((t) => t.status === "PUNT").length;
    const pendingCount = routineTasks.filter(
      (t) => t.status !== "COMPLETE" && t.status !== "PUNT"
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
      timeWindow: routine.time_window ?? null,
    });
  });

  tasksByDefinition.forEach((routineTasks, routineDefinitionId) => {
    const completedCount = routineTasks.filter((t) => t.status === "COMPLETE").length;
    const puntedCount = routineTasks.filter((t) => t.status === "PUNT").length;
    const pendingCount = routineTasks.filter(
      (t) => t.status !== "COMPLETE" && t.status !== "PUNT"
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
      timeWindow: null,
    });
  });

  return groups.filter((routine) => routine.pendingCount > 0);
};

interface RoutineGroupsListProps {
  tasks: Task[];
  routines: Routine[];
  expandedByDefault?: boolean;
  isCollapsable?: boolean;
  filterByAvailability?: boolean;
  collapseOutsideWindow?: boolean;
}

const getRoutineIcon = (name: string) => {
  const lowerName = name.toLowerCase();
  if (lowerName.includes("morning")) return faSun;
  if (lowerName.includes("evening") || lowerName.includes("night")) return faMoon;
  if (lowerName.includes("wellness") || lowerName.includes("health")) return faHeart;
  return faLeaf;
};

export const RoutineGroupsList: Component<RoutineGroupsListProps> = (props) => {
  const { setRoutineAction } = useStreamingData();
  const isCollapsable = () => props.isCollapsable ?? true;
  const shouldFilterByAvailability = () => props.filterByAvailability ?? false;
  const shouldCollapseOutsideWindow = () =>
    props.collapseOutsideWindow ?? false;
  const [expandedRoutines, setExpandedRoutines] = createSignal<Set<string>>(
    new Set()
  );
  const [now, setNow] = createSignal(new Date());
  const [pendingRoutine, setPendingRoutine] = createSignal<RoutineGroup | null>(
    null
  );

  onMount(() => {
    const interval = setInterval(() => {
      setNow(new Date());
    }, 30000);

    onCleanup(() => {
      clearInterval(interval);
    });
  });

  const visibleTasks = createMemo(() => filterVisibleTasks(props.tasks, now()));
  const routineGroups = createMemo(() =>
    buildRoutineGroups(visibleTasks(), props.routines)
  );

  const getRoutineDate = (routine: RoutineGroup) =>
    routine.tasks[0]?.scheduled_date ?? getDateString();

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
      Date.now() + minutes * 60 * 1000
    ).toISOString();
    await setRoutineAction(routine.routineId, routine.routineDefinitionId, {
      type: "SNOOZE",
      data: { snoozed_until: snoozedUntil },
    });
  };

  const getWindowTimes = (timeWindow: TimeWindow | null | undefined, date: string) => {
    const availableTime = timeWindow?.available_time
      ? getTime(date, timeWindow.available_time)
      : null;
    const startTime = timeWindow?.start_time
      ? getTime(date, timeWindow.start_time)
      : null;
    const endTime = timeWindow?.end_time ? getTime(date, timeWindow.end_time) : null;
    const cutoffTime = timeWindow?.cutoff_time
      ? getTime(date, timeWindow.cutoff_time)
      : null;

    return {
      availableTime,
      startTime,
      endTime,
      cutoffTime,
    };
  };

  const getAvailabilityStart = (times: ReturnType<typeof getWindowTimes>) =>
    times.availableTime ?? times.startTime ?? null;
  const getAvailabilityEnd = (times: ReturnType<typeof getWindowTimes>) =>
    times.cutoffTime ?? times.endTime ?? null;
  const getActiveStart = (times: ReturnType<typeof getWindowTimes>) =>
    times.startTime ?? null;
  const getActiveEnd = (times: ReturnType<typeof getWindowTimes>) =>
    times.endTime ?? times.cutoffTime ?? null;

  const getLatestTime = (left: Date | null, right: Date | null) => {
    if (!left) return right;
    if (!right) return left;
    return left > right ? left : right;
  };

  const getEarliestTime = (left: Date | null, right: Date | null) => {
    if (!left) return right;
    if (!right) return left;
    return left < right ? left : right;
  };

  const getEffectiveWindow = (
    routine: RoutineGroup,
    task: Task,
    date: string
  ) => {
    const routineTimes = getWindowTimes(routine.timeWindow, date);
    const taskTimes = getWindowTimes(task.time_window ?? null, date);

    const availabilityStart = getLatestTime(
      getAvailabilityStart(taskTimes),
      getAvailabilityStart(routineTimes)
    );
    const availabilityEnd = getEarliestTime(
      getAvailabilityEnd(taskTimes),
      getAvailabilityEnd(routineTimes)
    );
    const activeStart = getLatestTime(
      getActiveStart(taskTimes),
      getActiveStart(routineTimes)
    );
    const activeEnd = getEarliestTime(
      getActiveEnd(taskTimes),
      getActiveEnd(routineTimes)
    );

    if (
      availabilityStart &&
      availabilityEnd &&
      availabilityEnd < availabilityStart
    ) {
      return null;
    }

    if (activeStart && activeEnd && activeEnd < activeStart) {
      return {
        availabilityStart,
        availabilityEnd,
        activeStart: null,
        activeEnd: null,
      };
    }

    return {
      availabilityStart,
      availabilityEnd,
      activeStart,
      activeEnd,
    };
  };

  const getTaskWindowStatus = (
    routine: RoutineGroup,
    task: Task,
    currentTime: Date
  ): TaskWindowStatus => {
    if (task.status === "COMPLETE" || task.status === "PUNT") {
      return {
        isActive: false,
        isAvailable: false,
        isPastDue: false,
        nextAvailableTime: null as Date | null,
      };
    }

    const taskDate = task.scheduled_date ?? getRoutineDate(routine);
    const effectiveWindow = getEffectiveWindow(routine, task, taskDate);

    if (!effectiveWindow) {
      return {
        isActive: false,
        isAvailable: false,
        isPastDue: false,
        nextAvailableTime: null,
      };
    }

    const { availabilityStart, availabilityEnd, activeStart, activeEnd } =
      effectiveWindow;

    if (!availabilityStart && !availabilityEnd && !activeStart && !activeEnd) {
      return {
        isActive: false,
        isAvailable: true,
        isPastDue: false,
        nextAvailableTime: null,
      };
    }

    const isActive =
      Boolean(activeStart) &&
      currentTime >= (activeStart as Date) &&
      (!activeEnd || currentTime <= activeEnd);
    const isAvailable =
      !isActive &&
      (!availabilityStart || currentTime >= availabilityStart) &&
      (!availabilityEnd || currentTime <= availabilityEnd);
    const isPastDue = Boolean(availabilityEnd && currentTime > availabilityEnd);
    const nextAvailableTime =
      availabilityStart && currentTime < availabilityStart
        ? availabilityStart
        : null;

    return {
      isActive,
      isAvailable,
      isPastDue,
      nextAvailableTime,
    };
  };

  const getRoutineStatusInfo = (
    routine: RoutineGroup,
    currentTime: Date
  ): RoutineStatusInfo => {
    let hasActive = false;
    let hasAvailable = false;
    let hasPastDue = false;
    let nextAvailable: Date | null = null;

    routine.tasks.forEach((task) => {
      const status = getTaskWindowStatus(routine, task, currentTime);
      hasActive = hasActive || status.isActive;
      hasAvailable = hasAvailable || status.isAvailable;
      hasPastDue = hasPastDue || status.isPastDue;
      if (status.nextAvailableTime) {
        if (!nextAvailable || status.nextAvailableTime < nextAvailable) {
          nextAvailable = status.nextAvailableTime;
        }
      }
    });

    if (hasPastDue) {
      return { status: "past-due" as RoutineStatus, nextAvailableTime: null };
    }
    if (hasActive) {
      return { status: "active" as RoutineStatus, nextAvailableTime: null };
    }
    if (hasAvailable) {
      return { status: "available" as RoutineStatus, nextAvailableTime: null };
    }

    if (nextAvailable) {
      const diff = (nextAvailable as Date).getTime() - currentTime.getTime();
      if (diff <= UPCOMING_WINDOW_MS && diff > 0) {
        return { status: "inactive" as RoutineStatus, nextAvailableTime: nextAvailable };
      }
    }

    return { status: "hidden" as RoutineStatus, nextAvailableTime: nextAvailable };
  };

  const visibleRoutineGroups = createMemo(() => {
    const groups = routineGroups();
    if (!shouldFilterByAvailability()) return groups;
    const currentTime = now();
    return groups.filter(
      (routine) => getRoutineStatusInfo(routine, currentTime).status !== "hidden"
    );
  });

  const routineDefinitionIds = createMemo(() =>
    visibleRoutineGroups().map((group) => group.routineDefinitionId)
  );

  const routineDefinitionIdsInWindow = createMemo(() => {
    if (!shouldCollapseOutsideWindow()) return routineDefinitionIds();
    const currentTime = now();
    return visibleRoutineGroups()
      .filter(
        (group) => getRoutineStatusInfo(group, currentTime).status === "active"
      )
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
              ? Math.max(
                  0,
                  100 - completionPercentage() - puntedPercentage()
                )
              : 0;

          const isComplete = () => routine.completedCount === routine.totalCount;
          const isPunted = () =>
            routine.puntedCount === routine.totalCount && routine.puntedCount > 0;
          const isExpanded = () => isRoutineExpanded(routine.routineDefinitionId);
          const statusInfo = createMemo(() =>
            getRoutineStatusInfo(routine, now())
          );

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
            return "Hidden";
          };

          const getStatusPillClass = () => {
            const status = statusInfo().status;
            if (status === "active") return "bg-emerald-100/70 text-emerald-700";
            if (status === "available") return "bg-amber-100/80 text-amber-700";
            if (status === "past-due") return "bg-rose-100/80 text-rose-700";
            if (status === "inactive") return "bg-stone-100 text-stone-600";
            return "bg-stone-100 text-stone-600";
          };

          const getStatusClass = () => {
            if (isComplete())
              return "bg-gradient-to-br from-green-50 to-emerald-50";
            if (isPunted())
              return "bg-gradient-to-br from-red-50 to-rose-50";
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
                      { type: "COMPLETE" }
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
                      <Show when={statusInfo().status !== "hidden"}>
                        <span
                          class={`rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${getStatusPillClass()}`}
                        >
                          {getStatusLabel()}
                        </span>
                      </Show>
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
                        <Icon icon={faCircleCheck} class="w-4 h-4 fill-green-600" />
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
