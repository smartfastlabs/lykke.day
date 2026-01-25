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
import type { Routine, Task, TimeWindow } from "@/types/api";

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

  onMount(() => {
    const interval = setInterval(() => {
      setNow(new Date());
    }, 30000);

    onCleanup(() => {
      clearInterval(interval);
    });
  });

  const routineGroups = createMemo(() =>
    buildRoutineGroups(props.tasks, props.routines)
  );

  const getRoutineDate = (routine: RoutineGroup) =>
    routine.tasks[0]?.scheduled_date ?? getDateString();

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

  const isTaskActiveNow = (task: Task, currentTime: Date) => {
    if (task.status === "COMPLETE" || task.status === "PUNT") return false;
    if (!task.time_window) return false;
    const taskDate = task.scheduled_date;
    if (!taskDate) return false;

    const availableTime = task.time_window.available_time
      ? getTime(taskDate, task.time_window.available_time)
      : null;
    const startTime = task.time_window.start_time
      ? getTime(taskDate, task.time_window.start_time)
      : null;
    const endTime = task.time_window.end_time
      ? getTime(taskDate, task.time_window.end_time)
      : null;
    const cutoffTime = task.time_window.cutoff_time
      ? getTime(taskDate, task.time_window.cutoff_time)
      : null;

    const windowStart = startTime ?? availableTime;
    const windowEnd = endTime ?? cutoffTime;
    if (windowStart && currentTime < windowStart) return false;
    if (windowEnd && currentTime > windowEnd) return false;
    return true;
  };

  const getHasScheduledTasks = (routine: RoutineGroup) =>
    routine.tasks.some((task) => Boolean(task.time_window && task.scheduled_date));

  const isRoutineActiveFromTasks = (routine: RoutineGroup, currentTime: Date) =>
    routine.tasks.some((task) => isTaskActiveNow(task, currentTime));

  const isRoutineAvailableFromTimeWindow = (
    routine: RoutineGroup,
    currentTime: Date
  ) => {
    const routineDate = getRoutineDate(routine);
    const { availableTime, startTime, endTime, cutoffTime } = getWindowTimes(
      routine.timeWindow,
      routineDate
    );

    const availabilityStart = availableTime ?? startTime;
    const availabilityEnd = cutoffTime ?? endTime;

    if (availabilityStart && currentTime < availabilityStart) return false;
    if (availabilityEnd && currentTime > availabilityEnd) return false;
    return true;
  };

  const isRoutineInTimeWindow = (routine: RoutineGroup, currentTime: Date) => {
    const routineDate = getRoutineDate(routine);
    const { availableTime, startTime, endTime, cutoffTime } = getWindowTimes(
      routine.timeWindow,
      routineDate
    );

    const windowStart = startTime ?? availableTime;
    const windowEnd = endTime ?? cutoffTime;

    if (windowStart && currentTime < windowStart) return false;
    if (windowEnd && currentTime > windowEnd) return false;
    return true;
  };

  const isRoutineAvailable = (routine: RoutineGroup, currentTime: Date) => {
    if (routine.timeWindow) {
      return isRoutineAvailableFromTimeWindow(routine, currentTime);
    }
    if (!getHasScheduledTasks(routine)) {
      return true;
    }
    return isRoutineActiveFromTasks(routine, currentTime);
  };

  const isRoutineActiveWindow = (routine: RoutineGroup, currentTime: Date) => {
    if (routine.timeWindow) {
      return isRoutineInTimeWindow(routine, currentTime);
    }
    if (!getHasScheduledTasks(routine)) {
      return false;
    }
    return isRoutineActiveFromTasks(routine, currentTime);
  };

  const visibleRoutineGroups = createMemo(() => {
    const groups = routineGroups();
    if (!shouldFilterByAvailability()) return groups;
    const currentTime = now();
    return groups.filter((routine) => isRoutineAvailable(routine, currentTime));
  });

  const routineDefinitionIds = createMemo(() =>
    visibleRoutineGroups().map((group) => group.routineDefinitionId)
  );

  const routineDefinitionIdsInWindow = createMemo(() => {
    if (!shouldCollapseOutsideWindow()) return routineDefinitionIds();
    const currentTime = now();
    return visibleRoutineGroups()
      .filter((group) => isRoutineActiveWindow(group, currentTime))
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
    <div class="space-y-4">
      <Show when={visibleRoutineGroups().length === 0}>
        <div class="text-sm text-stone-500">No routines for today yet.</div>
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

          const getStatusClass = () => {
            if (isComplete())
              return "bg-gradient-to-br from-green-50 to-emerald-50";
            if (isPunted())
              return "bg-gradient-to-br from-red-50 to-rose-50";
            return "bg-amber-50/60 border border-amber-50/60";
          };

          const getSwipeableStatusClass = () => {
            if (isComplete())
              return "!bg-gradient-to-br !from-green-50 !to-emerald-50";
            if (isPunted())
              return "!bg-gradient-to-br !from-red-50 !to-rose-50";
            return "!bg-amber-50/60 !border !border-amber-50/60";
          };

          return (
            <div
              class={`rounded-xl p-4 transition-all duration-300 ${getStatusClass()}`}
            >
              <div class="-mx-4 -mt-4 mb-1">
                <SwipeableItem
                  onSwipeRight={() => {
                    if (!routine.routineId) return;
                    setRoutineAction(
                      routine.routineId,
                      routine.routineDefinitionId,
                      "COMPLETE"
                    );
                  }}
                  onSwipeLeft={() => {
                    if (!routine.routineId) return;
                    setRoutineAction(
                      routine.routineId,
                      routine.routineDefinitionId,
                      "PUNT"
                    );
                  }}
                  rightLabel="✅ Complete All Tasks"
                  leftLabel="🗑 Punt All Tasks"
                  statusClass={getSwipeableStatusClass()}
                >
                  <div
                    class="w-full flex items-start justify-between mb-3 text-left"
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
    </div>
  );
};

export default RoutineGroupsList;
