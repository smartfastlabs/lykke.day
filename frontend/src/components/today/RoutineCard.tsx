import { Component, For } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faDroplet, faSun, faMoon } from "@fortawesome/free-solid-svg-icons";
import type { Routine } from "@/types/api";

export interface RoutineCardProps {
  routines: Routine[];
  href: string;
}

export const RoutineCard: Component<RoutineCardProps> = (props) => (
  <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm md:col-span-2">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <Icon icon={faDroplet} class="w-5 h-5 fill-amber-600" />
        <p class="text-xs uppercase tracking-wide text-amber-700">Routines</p>
      </div>
      <a class="text-xs font-semibold text-amber-700 hover:text-amber-800" href={props.href}>
        See all routines
      </a>
    </div>
    <div class="grid sm:grid-cols-2 gap-4">
      <For each={props.routines}>
        {(routine) => (
          <div class="rounded-xl bg-amber-50/60 border border-amber-100 p-4">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <Icon
                  icon={routine.name.toLowerCase().includes("morning") ? faSun : faMoon}
                  class="w-4 h-4 fill-amber-700"
                />
                <p class="text-sm font-semibold text-stone-800">{routine.name}</p>
              </div>
              <span class="text-[11px] uppercase tracking-wide text-amber-700">
                {routine.category}
              </span>
            </div>
            <p class="text-xs text-stone-600 mb-3">{routine.description}</p>
          </div>
        )}
      </For>
    </div>
  </div>
);
