import { Component } from "solid-js";
import { useNavigate } from "@solidjs/router";
import { Icon } from "@/components/shared/Icon";
import {
  faLeaf,
  faPlus,
} from "@fortawesome/free-solid-svg-icons";
import type { Routine, Task } from "@/types/api";
import RoutineGroupsList from "@/components/routines/RoutineGroupsList";

export interface RoutineSummaryProps {
  tasks: Task[];
  routines: Routine[];
}

export const RoutineSummary: Component<RoutineSummaryProps> = (props) => {
  const navigate = useNavigate();

  return (
    <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-6 backdrop-blur-sm">
      <div class="flex items-center justify-between gap-3 mb-5">
        <button
          type="button"
          onClick={() => navigate("/me/today/routines")}
          class="flex items-center gap-3 text-left"
          aria-label="See all routines"
        >
          <Icon icon={faLeaf} class="w-5 h-5 fill-amber-600" />
          <p class="text-xs uppercase tracking-wide text-amber-700">Routines</p>
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
      <RoutineGroupsList
        tasks={props.tasks}
        routines={props.routines}
        filterByAvailability={true}
        collapseOutsideWindow={true}
      />
    </div>
  );
};
