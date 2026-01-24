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
  faPlus,
} from "@fortawesome/free-solid-svg-icons";
import type { RoutineDefinition, Task } from "@/types/api";
import { useStreamingData } from "@/providers/streamingData";
import { SwipeableItem } from "@/components/shared/SwipeableItem";
import TaskList from "@/components/tasks/List";
import { routineDefinitionAPI } from "@/utils/api";

export interface RoutineDefinitionsSummaryProps {
  tasks: Task[];
}

interface RoutineDefinitionGroup {
  routineDefinitionId: string;
  routineDefinitionName: string;
  tasks: Task[];
  completedCount: number;
  puntedCount: number;
  pendingCount: number;
  totalCount: number;
}

export const RoutineDefinitionsSummary: Component<RoutineDefinitionsSummaryProps> = (props) => {
  // Get routine definitions and actions from StreamingDataProvider
  const {
    routineDefinitions,
    setRoutineDefinitionAction,
    addRoutineDefinitionToToday,
  } = useStreamingData();

  // Track which routine definitions are expanded (persists across re-renders)
  const [expandedRoutineDefinitions, setExpandedRoutineDefinitions] =
    createSignal<Set<string>>(
    new Set()
  );
  const [showAddRoutine, setShowAddRoutine] = createSignal(false);
  const [isAddingRoutine, setIsAddingRoutine] = createSignal(false);
  const [fetchedRoutineDefinitions, setFetchedRoutineDefinitions] = createSignal<
    RoutineDefinition[]
  >([]);
  const [isLoadingRoutines, setIsLoadingRoutines] = createSignal(false);

  const toggleRoutineExpanded = (routineDefinitionId: string) => {
    setExpandedRoutineDefinitions((prev) => {
      const next = new Set(prev);
      if (next.has(routineDefinitionId)) {
        next.delete(routineDefinitionId);
      } else {
        next.add(routineDefinitionId);
      }
      return next;
    });
  };

  const isRoutineExpanded = (routineDefinitionId: string) => {
    return expandedRoutineDefinitions().has(routineDefinitionId);
  };

  const routineDefinitionSource = createMemo(() => {
    const routineDefinitionList = routineDefinitions() ?? [];
    if (routineDefinitionList.length > 0) {
      return routineDefinitionList;
    }
    return fetchedRoutineDefinitions();
  });

  // Create a map of routine definition ID to routine definition name
  const routineDefinitionMap = createMemo(() => {
    const map = new Map<string, string>();
    const routineDefinitionList = routineDefinitionSource();
    routineDefinitionList.forEach((routineDefinition) => {
      if (routineDefinition.id) {
        map.set(routineDefinition.id, routineDefinition.name);
      }
    });
    return map;
  });

  // Group tasks by routine_definition_id
  const routineDefinitionGroups = createMemo<RoutineDefinitionGroup[]>(() => {
    const groups = new Map<string, Task[]>();

    // Group tasks by routine_definition_id
    props.tasks.forEach((task) => {
      if (task.routine_definition_id) {
        if (!groups.has(task.routine_definition_id)) {
          groups.set(task.routine_definition_id, []);
        }
        groups.get(task.routine_definition_id)!.push(task);
      }
    });

    // Convert to array of RoutineDefinitionGroups
    const map = routineDefinitionMap();
    return Array.from(groups.entries())
      .map(([routineDefinitionId, tasks]) => {
        const completedCount = tasks.filter(
          (t) => t.status === "COMPLETE"
        ).length;
        const puntedCount = tasks.filter((t) => t.status === "PUNT").length;
        const pendingCount = tasks.filter(
          (t) => t.status !== "COMPLETE" && t.status !== "PUNT"
        ).length;

        // Get the routine definition name from the map
        const routineDefinitionName =
          map.get(routineDefinitionId) || "Routine Definition";

        return {
          routineDefinitionId,
          routineDefinitionName,
          tasks,
          completedCount,
          puntedCount,
          pendingCount,
          totalCount: tasks.length,
        };
      })
      .filter((routineDefinition) => {
        // Hide routine definitions where every task is complete or punted
        return routineDefinition.pendingCount > 0;
      });
  });

  const hasRoutineDefinitions = createMemo(
    () => routineDefinitionGroups().length > 0
  );
  const routineDefinitionIdsInTasks = createMemo(() => {
    const ids = new Set<string>();
    props.tasks.forEach((task) => {
      if (task.routine_definition_id) {
        ids.add(task.routine_definition_id);
      }
    });
    return ids;
  });
  const availableRoutineDefinitions = createMemo(() => {
    const routineDefinitionList = routineDefinitionSource();
    const usedIds = routineDefinitionIdsInTasks();
    return routineDefinitionList.filter(
      (routineDefinition) =>
        routineDefinition.id && !usedIds.has(routineDefinition.id)
    );
  });

  const getRoutineIcon = (name: string) => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes("morning")) return faSun;
    if (lowerName.includes("evening") || lowerName.includes("night"))
      return faMoon;
    if (lowerName.includes("wellness") || lowerName.includes("health"))
      return faHeart;
    return faLeaf;
  };

  const handleAddRoutineDefinition = async (routineDefinitionId: string) => {
    if (isAddingRoutine()) return;
    setIsAddingRoutine(true);
    try {
      await addRoutineDefinitionToToday(routineDefinitionId);
      setShowAddRoutine(false);
    } finally {
      setIsAddingRoutine(false);
    }
  };

  const handleOpenAddRoutine = async () => {
    setShowAddRoutine(true);
    if (isLoadingRoutines()) return;
    if (
      (routineDefinitions() ?? []).length > 0 ||
      fetchedRoutineDefinitions().length > 0
    )
      return;

    setIsLoadingRoutines(true);
    try {
      const fetched = await routineDefinitionAPI.getAll();
      setFetchedRoutineDefinitions(fetched);
    } finally {
      setIsLoadingRoutines(false);
    }
  };

  return (
    <>
      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-6 backdrop-blur-sm">
        <div class="flex items-center justify-between gap-3 mb-5">
          <div class="flex items-center gap-3">
            <Icon icon={faLeaf} class="w-5 h-5 fill-amber-600" />
            <h3 class="text-lg font-semibold text-stone-800">
              Routine Definitions
            </h3>
          </div>
          <button
            type="button"
            onClick={handleOpenAddRoutine}
            class="inline-flex items-center justify-center w-9 h-9 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-600/80 transition hover:bg-amber-100/80 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Add routine definition"
            title="Add routine definition"
          >
            <Icon icon={faPlus} class="w-4 h-4 fill-amber-600/80" />
          </button>
        </div>

        <div class="space-y-4">
          <Show when={!hasRoutineDefinitions()}>
            <div class="text-sm text-stone-500">
              No routine definitions for today yet. Add one to get started.
            </div>
          </Show>
          <For each={routineDefinitionGroups()}>
            {(routineDefinition) => {
              const completionPercentage = () =>
                routineDefinition.totalCount > 0
                  ? Math.round(
                      (routineDefinition.completedCount /
                        routineDefinition.totalCount) *
                        100
                    )
                  : 0;

              const puntedPercentage = () =>
                routineDefinition.totalCount > 0
                  ? Math.round(
                      (routineDefinition.puntedCount /
                        routineDefinition.totalCount) *
                        100
                    )
                  : 0;

              const pendingPercentage = () =>
                routineDefinition.totalCount > 0
                  ? Math.max(
                      0,
                      100 - completionPercentage() - puntedPercentage()
                    )
                  : 0;

              const isComplete = () =>
                routineDefinition.completedCount ===
                routineDefinition.totalCount;

              const isPunted = () =>
                routineDefinition.puntedCount ===
                  routineDefinition.totalCount &&
                routineDefinition.puntedCount > 0;

              const isExpanded = () =>
                isRoutineExpanded(routineDefinition.routineDefinitionId);

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
                  {/* Routine Header - Swipeable */}
                  <div class="-mx-4 -mt-4 mb-1">
                    <SwipeableItem
                      onSwipeRight={() =>
                        setRoutineDefinitionAction(
                          routineDefinition.routineDefinitionId,
                          "COMPLETE"
                        )
                      }
                      onSwipeLeft={() =>
                        setRoutineDefinitionAction(
                          routineDefinition.routineDefinitionId,
                          "PUNT"
                        )
                      }
                      rightLabel="✅ Complete All Tasks"
                      leftLabel="🗑 Punt All Tasks"
                      statusClass={getSwipeableStatusClass()}
                    >
                      <button
                        class="w-full flex items-start justify-between mb-3 text-left"
                        onClick={() =>
                          toggleRoutineExpanded(
                            routineDefinition.routineDefinitionId
                          )
                        }
                      >
                      <div class="flex items-center gap-2">
                        <Icon
                          icon={isExpanded() ? faChevronDown : faChevronRight}
                          class={`w-3 h-3 transition-transform duration-200 ${isComplete() ? "fill-green-600" : isPunted() ? "fill-red-600" : "fill-amber-700"}`}
                        />
                        <Icon
                          icon={getRoutineIcon(
                            routineDefinition.routineDefinitionName
                          )}
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
                          {routineDefinition.routineDefinitionName}
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
                          {routineDefinition.completedCount}/
                          {routineDefinition.totalCount}
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

                  {/* Progress Bar */}
                  <Show
                    when={
                      routineDefinition.totalCount > 0 &&
                      (routineDefinition.completedCount > 0 ||
                        routineDefinition.puntedCount > 0)
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

                  {/* Task List - Collapsible */}
                  <Show when={isExpanded()}>
                    <div class="space-y-1.5 mt-3 transition-opacity duration-300 ease-in-out">
                      <TaskList tasks={() => routineDefinition.tasks} />
                    </div>
                  </Show>
                </div>
              );
            }}
          </For>
        </div>
      </div>
      <Show when={showAddRoutine()}>
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 px-4">
          <div class="w-full max-w-md rounded-2xl bg-white shadow-xl shadow-amber-900/10 border border-white/70">
            <div class="flex items-center justify-between px-5 py-4 border-b border-stone-100">
              <h4 class="text-base font-semibold text-stone-800">
                Add a routine definition
              </h4>
              <button
                type="button"
                onClick={() => setShowAddRoutine(false)}
                class="text-stone-400 hover:text-stone-600 transition"
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <div class="p-4 space-y-2 max-h-80 overflow-y-auto">
              <Show
                when={isLoadingRoutines()}
                fallback={
                  <Show
                    when={availableRoutineDefinitions().length > 0}
                    fallback={
                      <div class="text-sm text-stone-500">
                        {routineDefinitionSource().length === 0
                          ? "No routine definitions created yet."
                          : "All routine definitions are already on today's list."}
                      </div>
                    }
                  >
                    <For each={availableRoutineDefinitions()}>
                      {(routineDefinition) => (
                        <button
                          type="button"
                          onClick={() =>
                            routineDefinition.id &&
                            handleAddRoutineDefinition(routineDefinition.id)
                          }
                          disabled={
                            isAddingRoutine() || !routineDefinition.id
                          }
                          class="w-full text-left px-4 py-3 rounded-xl border border-amber-100/70 bg-amber-50/40 text-stone-700 hover:bg-amber-50/70 transition disabled:opacity-60 disabled:cursor-not-allowed"
                        >
                          <div class="font-medium">
                            {routineDefinition.name}
                          </div>
                          <Show when={routineDefinition.description}>
                            <div class="text-xs text-stone-500 mt-1">
                              {routineDefinition.description}
                            </div>
                          </Show>
                        </button>
                      )}
                    </For>
                  </Show>
                }
              >
                <div class="text-sm text-stone-500">
                  Loading routine definitions...
                </div>
              </Show>
            </div>
          </div>
        </div>
      </Show>
    </>
  );
};
