import { Component, Show, createMemo } from "solid-js";
import { useNavigate } from "@solidjs/router";
import { Icon } from "@/components/shared/Icon";
import { faLeaf, faPlus } from "@fortawesome/free-solid-svg-icons";
import type { Routine, Task } from "@/types/api";
import RoutineGroupsList from "@/components/routines/RoutineGroupsList";
import { buildRoutineGroups } from "@/components/routines/RoutineGroupsList";
import { filterVisibleTasks } from "@/utils/tasks";
import { FuzzyCard, FuzzyLine } from "./FuzzyCard";

export interface RoutineSummaryProps {
  tasks: Task[];
  routines: Routine[];
  isLoading?: boolean;
}

export const RoutineSummary: Component<RoutineSummaryProps> = (props) => {
  const navigate = useNavigate();

  const allGroups = createMemo(() =>
    buildRoutineGroups(filterVisibleTasks(props.tasks), props.routines),
  );

  const counts = createMemo(() => {
    const groups = allGroups();
    const total = groups.length;
    const done = groups.filter(
      (g) => g.totalCount > 0 && g.completedCount === g.totalCount,
    ).length;
    const hidden = groups.filter(
      (g) => (g.timing_status ?? "hidden") === "hidden",
    ).length;
    const showingNow = groups.filter(
      (g) => g.pendingCount > 0 && (g.timing_status ?? "hidden") !== "hidden",
    ).length;
    const notShown = Math.max(0, total - showingNow);
    return { total, done, hidden, showingNow, notShown };
  });

  return (
    <Show
      when={!props.isLoading}
      fallback={
        <FuzzyCard class="p-4 space-y-3">
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="h-4 w-4 rounded-full bg-amber-200/90" />
              <FuzzyLine class="h-2 w-20" />
            </div>
            <div class="h-9 w-9 rounded-full bg-amber-100/90" />
          </div>
          <div class="space-y-2">
            <FuzzyLine class="h-3 w-full" />
            <FuzzyLine class="h-3 w-5/6" />
            <FuzzyLine class="h-3 w-4/6" />
          </div>
        </FuzzyCard>
      }
    >
      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-4 backdrop-blur-sm">
        <div class="flex items-center justify-between gap-3 mb-3">
          <button
            type="button"
            onClick={() => navigate("/me/today/routines")}
            class="flex items-center gap-3 text-left"
            aria-label="See all routines"
          >
            <Icon icon={faLeaf} class="w-5 h-5 fill-amber-600" />
            <p class="text-xs uppercase tracking-wide text-amber-700">
              Routines
            </p>
          </button>
          <div class="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate("/me/today/routines")}
              class="inline-flex items-center justify-center w-9 h-9 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-600/80 transition hover:bg-amber-100/80 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Add routine"
              title="Add routine"
            >
              <Icon icon={faPlus} class="w-4 h-4 fill-amber-600/80" />
            </button>
          </div>
        </div>
        <Show when={counts().total > 0 && counts().notShown > 0}>
          <button
            type="button"
            onClick={() => navigate("/me/today/routines")}
            class="mb-3 text-left text-xs text-stone-600 hover:text-stone-800"
            aria-label="See hidden routines"
          >
            Showing {counts().showingNow} now · {counts().done} done ·{" "}
            {counts().hidden} later ·{" "}
            <span class="underline underline-offset-2">See all</span>
          </button>
        </Show>
        <RoutineGroupsList
          tasks={props.tasks}
          routines={props.routines}
          filterByAvailability={true}
          filterByPending={true}
          collapseOutsideWindow={true}
        />
      </div>
    </Show>
  );
};
