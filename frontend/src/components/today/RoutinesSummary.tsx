import { Component, createMemo, createSignal, For, Show } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import {
  faCircleCheck,
  faCircle,
  faSun,
  faMoon,
  faLeaf,
  faHeart,
  faChevronDown,
  faChevronRight,
  faForward,
} from "@fortawesome/free-solid-svg-icons";
import type { Task } from "@/types/api";
import { useStreamingData } from "@/providers/streaming-data";
import { SwipeableItem } from "@/components/shared/SwipeableItem";

export interface RoutinesSummaryProps {
  tasks: Task[];
}

interface RoutineGroup {
  routineId: string;
  routineName: string;
  tasks: Task[];
  completedCount: number;
  puntedCount: number;
  totalCount: number;
}

export const RoutinesSummary: Component<RoutinesSummaryProps> = (props) => {
  // Get routines, setTaskStatus, and setRoutineAction from StreamingDataProvider
  const { routines, setTaskStatus, setRoutineAction } = useStreamingData();

  // Track which routines are expanded (persists across re-renders)
  const [expandedRoutines, setExpandedRoutines] = createSignal<Set<string>>(
    new Set()
  );

  const toggleRoutineExpanded = (routineId: string) => {
    setExpandedRoutines((prev) => {
      const next = new Set(prev);
      if (next.has(routineId)) {
        next.delete(routineId);
      } else {
        next.add(routineId);
      }
      return next;
    });
  };

  const isRoutineExpanded = (routineId: string) => {
    return expandedRoutines().has(routineId);
  };

  // Create a map of routine ID to routine name
  const routineMap = createMemo(() => {
    const map = new Map<string, string>();
    const routineList = routines();
    if (routineList) {
      routineList.forEach((routine) => {
        if (routine.id) {
          map.set(routine.id, routine.name);
        }
      });
    }
    return map;
  });

  // Group tasks by routine_id
  const routineGroups = createMemo<RoutineGroup[]>(() => {
    const groups = new Map<string, Task[]>();

    // Group tasks by routine_id
    props.tasks.forEach((task) => {
      if (task.routine_id) {
        if (!groups.has(task.routine_id)) {
          groups.set(task.routine_id, []);
        }
        groups.get(task.routine_id)!.push(task);
      }
    });

    // Convert to array of RoutineGroups
    const map = routineMap();
    return Array.from(groups.entries()).map(([routineId, tasks]) => {
      const completedCount = tasks.filter(
        (t) => t.status === "COMPLETE"
      ).length;
      const puntedCount = tasks.filter((t) => t.status === "PUNT").length;

      // Get the routine name from the routines map
      const routineName = map.get(routineId) || "Routine";

      return {
        routineId,
        routineName,
        tasks,
        completedCount,
        puntedCount,
        totalCount: tasks.length,
      };
    });
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
    <Show when={hasRoutines()}>
      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-6 backdrop-blur-sm">
        <div class="flex items-center gap-3 mb-5">
          <Icon icon={faLeaf} class="w-5 h-5 fill-amber-600" />
          <h3 class="text-lg font-semibold text-stone-800">Routines</h3>
        </div>

        <div class="space-y-4">
          <For each={routineGroups()}>
            {(routine) => {
              const completionPercentage = () =>
                routine.totalCount > 0
                  ? Math.round(
                      (routine.completedCount / routine.totalCount) * 100
                    )
                  : 0;

              const isComplete = () =>
                routine.completedCount === routine.totalCount;

              const isPunted = () =>
                routine.puntedCount === routine.totalCount &&
                routine.puntedCount > 0;

              const isExpanded = () => isRoutineExpanded(routine.routineId);

              const getStatusClass = () => {
                if (isComplete())
                  return "bg-gradient-to-br from-green-50 to-emerald-50";
                if (isPunted())
                  return "bg-gradient-to-br from-red-50 to-rose-50";
                return "bg-amber-50/60 border border-amber-100";
              };

              return (
                <div
                  class={`rounded-xl p-4 transition-all duration-300 ${getStatusClass()}`}
                >
                  {/* Routine Header - Swipeable */}
                  <div class="-mx-4 -mt-4 mb-1">
                    <SwipeableItem
                      onSwipeRight={() => setRoutineAction(routine.routineId, "COMPLETE")}
                      onSwipeLeft={() => setRoutineAction(routine.routineId, "PUNT")}
                      rightLabel="✅ Complete All Tasks"
                      leftLabel="🗑 Punt All Tasks"
                      statusClass={getStatusClass()}
                    >
                      <button
                        class="w-full flex items-start justify-between mb-3 text-left"
                        onClick={() => toggleRoutineExpanded(routine.routineId)}
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

                  {/* Progress Bar */}
                  <div class="relative w-full h-1.5 bg-white/80 rounded-full overflow-hidden mb-3">
                    <div
                      class="absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out"
                      classList={{
                        "bg-gradient-to-r from-green-400 to-emerald-500":
                          isComplete(),
                        "bg-gradient-to-r from-red-400 to-rose-500":
                          isPunted(),
                        "bg-gradient-to-r from-amber-400 to-orange-500":
                          !isComplete() && !isPunted(),
                      }}
                      style={{
                        width: `${completionPercentage()}%`,
                      }}
                    />
                  </div>

                  {/* Task List - Collapsible */}
                  <Show when={isExpanded()}>
                    <div class="space-y-1.5 mt-3 transition-opacity duration-300 ease-in-out">
                      <For each={routine.tasks}>
                        {(task) => {
                          const isTaskComplete = () =>
                            task.status === "COMPLETE";
                          const isTaskPunted = () => task.status === "PUNT";
                          // Extract just the task name after the routine prefix and dash
                          const taskDisplayName = () => {
                            let displayName = task.name;
                            // Remove "Routine: " prefix
                            displayName = displayName.replace(
                              /^Routine:\s*/i,
                              ""
                            );
                            // Remove routine name and dash if present (e.g., "Morning - Task" -> "Task")
                            const dashIndex = displayName.indexOf(" - ");
                            if (dashIndex > 0) {
                              displayName = displayName.substring(
                                dashIndex + 3
                              );
                            }
                            return displayName;
                          };

                          const getTaskIcon = () => {
                            if (isTaskComplete()) return faCircleCheck;
                            if (isTaskPunted()) return faForward;
                            return faCircle;
                          };

                          const getStatusClass = () => {
                            if (isTaskComplete())
                              return "bg-green-50/60 border-green-100";
                            if (isTaskPunted())
                              return "bg-orange-50/60 border-orange-100";
                            return "";
                          };

                          return (
                            <SwipeableItem
                              onSwipeRight={() =>
                                setTaskStatus(task, "COMPLETE")
                              }
                              onSwipeLeft={() => setTaskStatus(task, "PUNT")}
                              rightLabel="✅ Complete"
                              leftLabel="🗑 Punt"
                              statusClass={getStatusClass()}
                              compact={true}
                            >
                              <div class="flex items-center gap-2 text-xs">
                                <Icon
                                  icon={getTaskIcon()}
                                  class={`w-3 h-3 flex-shrink-0 ${isTaskComplete() ? "fill-green-600" : isTaskPunted() ? "fill-orange-500" : "fill-stone-300"}`}
                                />
                                <span
                                  class="leading-tight"
                                  classList={{
                                    "text-green-700 line-through":
                                      isTaskComplete(),
                                    "text-orange-600 italic": isTaskPunted(),
                                    "text-stone-600":
                                      !isTaskComplete() && !isTaskPunted(),
                                  }}
                                >
                                  {taskDisplayName()}
                                  {isTaskPunted() && (
                                    <span class="ml-1 text-[10px] text-orange-500">
                                      (punted)
                                    </span>
                                  )}
                                </span>
                              </div>
                            </SwipeableItem>
                          );
                        }}
                      </For>
                    </div>
                  </Show>
                </div>
              );
            }}
          </For>
        </div>
      </div>
    </Show>
  );
};
