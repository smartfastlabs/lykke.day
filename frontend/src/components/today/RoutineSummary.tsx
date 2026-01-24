import { Component, createMemo, createSignal, For, Show } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import {
  faCircleCheck,
  faSun,
  faMoon,
  faLeaf,
  faHeart,
  faChevronDown,
  faChevronRight,
} from "@fortawesome/free-solid-svg-icons";
import type { Routine, Task } from "@/types/api";
import { useStreamingData } from "@/providers/streamingData";
import { SwipeableItem } from "@/components/shared/SwipeableItem";
import TaskList from "@/components/tasks/List";

export interface RoutineSummaryProps {
  tasks: Task[];
  routines: Routine[];
}

interface RoutineGroup {
  routineDefinitionId: string;
  routineName: string;
  tasks: Task[];
  completedCount: number;
  puntedCount: number;
  pendingCount: number;
  totalCount: number;
}

export const RoutineSummary: Component<RoutineSummaryProps> = (props) => {
  const { setRoutineAction } = useStreamingData();

  const [expandedRoutines, setExpandedRoutines] = createSignal<Set<string>>(
    new Set()
  );

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
    expandedRoutines().has(routineDefinitionId);

  const routineMap = createMemo(() => {
    const map = new Map<string, Routine>();
    props.routines.forEach((routine) => {
      map.set(routine.routine_definition_id, routine);
    });
    return map;
  });

  const routineGroups = createMemo<RoutineGroup[]>(() => {
    const groups = new Map<string, Task[]>();

    props.tasks.forEach((task) => {
      if (task.routine_definition_id) {
        if (!groups.has(task.routine_definition_id)) {
          groups.set(task.routine_definition_id, []);
        }
        groups.get(task.routine_definition_id)!.push(task);
      }
    });

    const routinesByDefinition = routineMap();
    return Array.from(groups.entries())
      .map(([routineDefinitionId, tasks]) => {
        const completedCount = tasks.filter(
          (t) => t.status === "COMPLETE"
        ).length;
        const puntedCount = tasks.filter((t) => t.status === "PUNT").length;
        const pendingCount = tasks.filter(
          (t) => t.status !== "COMPLETE" && t.status !== "PUNT"
        ).length;
        const routineName =
          routinesByDefinition.get(routineDefinitionId)?.name ?? "Routine";

        return {
          routineDefinitionId,
          routineName,
          tasks,
          completedCount,
          puntedCount,
          pendingCount,
          totalCount: tasks.length,
        };
      })
      .filter((routine) => routine.pendingCount > 0);
  });

  const hasRoutines = createMemo(() => routineGroups().length > 0);

  const getRoutineIcon = (name: string) => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes("morning")) return faSun;
    if (lowerName.includes("evening") || lowerName.includes("night"))
      return faMoon;
    if (lowerName.includes("wellness") || lowerName.includes("health"))
      return faHeart;
    return faLeaf;
  };

  return (
    <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-6 backdrop-blur-sm">
      <div class="flex items-center justify-between gap-3 mb-5">
        <div class="flex items-center gap-3">
          <Icon icon={faLeaf} class="w-5 h-5 fill-amber-600" />
          <h3 class="text-lg font-semibold text-stone-800">Routines</h3>
        </div>
      </div>

      <div class="space-y-4">
        <Show when={!hasRoutines()}>
          <div class="text-sm text-stone-500">
            No routines for today yet.
          </div>
        </Show>
        <For each={routineGroups()}>
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

            const isComplete = () =>
              routine.completedCount === routine.totalCount;

            const isPunted = () =>
              routine.puntedCount === routine.totalCount &&
              routine.puntedCount > 0;

            const isExpanded = () =>
              isRoutineExpanded(routine.routineDefinitionId);

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
                    onSwipeRight={() =>
                      setRoutineAction(routine.routineDefinitionId, "COMPLETE")
                    }
                    onSwipeLeft={() =>
                      setRoutineAction(routine.routineDefinitionId, "PUNT")
                    }
                    rightLabel="✅ Complete All Tasks"
                    leftLabel="🗑 Punt All Tasks"
                    statusClass={getSwipeableStatusClass()}
                  >
                    <button
                      class="w-full flex items-start justify-between mb-3 text-left"
                      onClick={() =>
                        toggleRoutineExpanded(routine.routineDefinitionId)
                      }
                    >
                      <div class="flex items-center gap-2">
                        <Icon
                          icon={isExpanded() ? faChevronDown : faChevronRight}
                          class={`w-3 h-3 transition-transform duration-200 ${isComplete() ? "fill-green-600" : isPunted() ? "fill-red-600" : "fill-amber-700"}`}
                        />
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
                          <Icon
                            icon={faCircleCheck}
                            class="w-4 h-4 fill-green-600"
                          />
                        </Show>
                      </div>
                    </button>
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
    </div>
  );
};
