import { Component, For, type Accessor } from "solid-js";

interface StatItem {
  label: string;
  value: number;
  colorClasses?: string;
}

interface StatsCardProps {
  title: string;
  completionPercentage: Accessor<number>;
  stats: Accessor<StatItem[]>;
}

export const StatsCard: Component<StatsCardProps> = (props) => {
  return (
    <div class="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl shadow-xl shadow-amber-900/5 p-6 md:p-8">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl md:text-2xl font-semibold text-stone-800">
          {props.title}
        </h2>
        <div class="flex items-baseline gap-1">
          <span class="text-3xl font-bold text-amber-600">
            {props.completionPercentage()}
          </span>
          <span class="text-stone-500 text-lg">%</span>
        </div>
      </div>

      {/* Progress bar */}
      <div class="relative w-full h-3 bg-stone-100 rounded-full overflow-hidden mb-6">
        <div
          class="absolute inset-y-0 left-0 bg-gradient-to-r from-amber-400 to-orange-500 rounded-full transition-all duration-500 ease-out"
          style={{
            width: `${props.completionPercentage()}%`,
          }}
        />
      </div>

      {/* Stats grid */}
      <div class="grid grid-cols-4 gap-3">
        <For each={props.stats()}>
          {(stat: StatItem) => (
            <div
              class={`text-center p-3 rounded-xl border ${
                stat.colorClasses ??
                "bg-white/50 border-stone-100 text-stone-800"
              }`}
            >
              <div class="text-2xl font-bold">{stat.value}</div>
              <div class="text-xs mt-1">{stat.label}</div>
            </div>
          )}
        </For>
      </div>
    </div>
  );
};
