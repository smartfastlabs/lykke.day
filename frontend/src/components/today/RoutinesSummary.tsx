import { Component, createMemo, createResource, createSignal, For, Show } from "solid-js";
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
import type { Task, Routine } from "@/types/api";
import { routineAPI } from "@/utils/api";

export interface RoutinesSummaryProps {
  tasks: Task[];
}

interface RoutineGroup {
  routineId: string;
  routineName: string;
  tasks: Task[];
  completedCount: number;
  totalCount: number;
}

export const RoutinesSummary: Component<RoutinesSummaryProps> = (props) => {
  // Fetch all routines
  const [routines] = createResource<Routine[]>(routineAPI.getAll);

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
      const completedCount = tasks.filter((t) => t.status === "COMPLETE").length;
      
      // Get the routine name from the routines map
      const routineName = map.get(routineId) || "Routine";

      return {
        routineId,
        routineName,
        tasks,
        completedCount,
        totalCount: tasks.length,
      };
    });
  });

  const hasRoutines = createMemo(() => routineGroups().length > 0);

  const getRoutineIcon = (name: string) => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes("morning")) return faSun;
    if (lowerName.includes("evening") || lowerName.includes("night")) return faMoon;
    if (lowerName.includes("wellness") || lowerName.includes("health")) return faHeart;
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
              const [isExpanded, setIsExpanded] = createSignal(false);
              const completionPercentage = () =>
                routine.totalCount > 0
                  ? Math.round((routine.completedCount / routine.totalCount) * 100)
                  : 0;

              const isComplete = () => routine.completedCount === routine.totalCount;

              return (
                <div
                  class="rounded-xl p-4 transition-all duration-300"
                  classList={{
                    "bg-gradient-to-br from-green-50 to-emerald-50 border border-green-100":
                      isComplete(),
                    "bg-amber-50/60 border border-amber-100": !isComplete(),
                  }}
                >
                  {/* Routine Header - Clickable */}
                  <button
                    class="w-full flex items-start justify-between mb-3 text-left"
                    onClick={() => setIsExpanded(!isExpanded())}
                  >
                    <div class="flex items-center gap-2">
                      <Icon
                        icon={isExpanded() ? faChevronDown : faChevronRight}
                        class="w-3 h-3 transition-transform duration-200"
                        classList={{
                          "fill-green-600": isComplete(),
                          "fill-amber-700": !isComplete(),
                        }}
                      />
                      <Icon
                        icon={getRoutineIcon(routine.routineName)}
                        class="w-4 h-4"
                        classList={{
                          "fill-green-600": isComplete(),
                          "fill-amber-700": !isComplete(),
                        }}
                      />
                      <span
                        class="text-sm font-semibold"
                        classList={{
                          "text-green-700": isComplete(),
                          "text-stone-800": !isComplete(),
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
                          "text-amber-700": !isComplete(),
                        }}
                      >
                        {routine.completedCount}/{routine.totalCount}
                      </span>
                      <Show when={isComplete()}>
                        <Icon icon={faCircleCheck} class="w-4 h-4 fill-green-600" />
                      </Show>
                    </div>
                  </button>

                  {/* Progress Bar */}
                  <div class="relative w-full h-1.5 bg-white/80 rounded-full overflow-hidden mb-3">
                    <div
                      class="absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out"
                      classList={{
                        "bg-gradient-to-r from-green-400 to-emerald-500": isComplete(),
                        "bg-gradient-to-r from-amber-400 to-orange-500": !isComplete(),
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
                          const isTaskComplete = () => task.status === "COMPLETE";
                          const isTaskPunted = () => task.status === "PUNT";
                          // Extract just the task name after the routine prefix and dash
                          const taskDisplayName = () => {
                            let displayName = task.name;
                            // Remove "Routine: " prefix
                            displayName = displayName.replace(/^Routine:\s*/i, "");
                            // Remove routine name and dash if present (e.g., "Morning - Task" -> "Task")
                            const dashIndex = displayName.indexOf(" - ");
                            if (dashIndex > 0) {
                              displayName = displayName.substring(dashIndex + 3);
                            }
                            return displayName;
                          };

                          const getTaskIcon = () => {
                            if (isTaskComplete()) return faCircleCheck;
                            if (isTaskPunted()) return faForward;
                            return faCircle;
                          };

                          return (
                            <div class="flex items-center gap-2 text-xs">
                              <Icon
                                icon={getTaskIcon()}
                                class="w-3 h-3 flex-shrink-0"
                                classList={{
                                  "fill-green-600": isTaskComplete(),
                                  "fill-orange-500": isTaskPunted(),
                                  "fill-stone-300": !isTaskComplete() && !isTaskPunted(),
                                }}
                              />
                              <span
                                class="leading-tight"
                                classList={{
                                  "text-green-700 line-through": isTaskComplete(),
                                  "text-orange-600 italic": isTaskPunted(),
                                  "text-stone-600": !isTaskComplete() && !isTaskPunted(),
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
