import { Component, createSignal, onMount, Show } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import TaskList from "@/components/tasks/List";
import { Task } from "@/types/api";

const getTaskStats = (tasks: Task[]) => {
  const total = tasks.length;
  const completed = tasks.filter((t) => t.status === "COMPLETE").length;
  const pending = tasks.filter((t) => t.status === "PENDING").length;
  const punted = tasks.filter((t) => t.status === "PUNT").length;
  return { total, completed, pending, punted };
};

export const TodaysTasksView: Component = () => {
  const { tasks } = useSheppard();
  const [mounted, setMounted] = createSignal(false);

  onMount(() => {
    setTimeout(() => setMounted(true), 50);
  });

  const stats = () => getTaskStats(tasks());
  const completionPercentage = () => {
    const s = stats();
    return s.total > 0 ? Math.round((s.completed / s.total) * 100) : 0;
  };

  return (
    <div class="w-full">
      {/* Stats card */}
      <div
        class="mb-8 transition-all duration-1000 delay-200 ease-out"
        style={{
          opacity: mounted() ? 1 : 0,
          transform: mounted() ? "translateY(0)" : "translateY(20px)",
        }}
      >
        <div class="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl shadow-xl shadow-amber-900/5 p-6 md:p-8">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl md:text-2xl font-semibold text-stone-800">
              Today's Progress
            </h2>
            <div class="flex items-baseline gap-1">
              <span class="text-3xl font-bold text-amber-600">
                {completionPercentage()}
              </span>
              <span class="text-stone-500 text-lg">%</span>
            </div>
          </div>

          {/* Progress bar */}
          <div class="relative w-full h-3 bg-stone-100 rounded-full overflow-hidden mb-6">
            <div
              class="absolute inset-y-0 left-0 bg-gradient-to-r from-amber-400 to-orange-500 rounded-full transition-all duration-500 ease-out"
              style={{
                width: `${completionPercentage()}%`,
              }}
            />
          </div>

          {/* Stats grid */}
          <div class="grid grid-cols-3 gap-4">
            <div class="text-center p-3 bg-white/50 rounded-xl border border-stone-100">
              <div class="text-2xl font-bold text-stone-800">
                {stats().total}
              </div>
              <div class="text-xs text-stone-500 mt-1">Total</div>
            </div>
            <div class="text-center p-3 bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border border-green-100">
              <div class="text-2xl font-bold text-green-700">
                {stats().completed}
              </div>
              <div class="text-xs text-green-600 mt-1">Completed</div>
            </div>
            <div class="text-center p-3 bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-100">
              <div class="text-2xl font-bold text-amber-700">
                {stats().pending}
              </div>
              <div class="text-xs text-amber-600 mt-1">Pending</div>
            </div>
          </div>

          <Show when={stats().punted > 0}>
            <div class="mt-4 p-3 bg-stone-50 rounded-xl border border-stone-200 text-center">
              <span class="text-sm text-stone-600">
                <span class="font-semibold">{stats().punted}</span> task
                {stats().punted !== 1 ? "s" : ""} punted for later
              </span>
            </div>
          </Show>
        </div>
      </div>

      {/* Tasks section */}
      <div
        class="transition-all duration-1000 delay-300 ease-out"
        style={{
          opacity: mounted() ? 1 : 0,
          transform: mounted() ? "translateY(0)" : "translateY(20px)",
        }}
      >
        <div class="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl shadow-xl shadow-amber-900/5 overflow-hidden">
          <div class="px-6 py-5 border-b border-stone-100">
            <h2 class="text-xl md:text-2xl font-semibold text-stone-800">
              Your Tasks
            </h2>
            <p class="text-sm text-stone-500 mt-1">
              Swipe right to complete, left to punt
            </p>
          </div>

          <div class="p-4">
            <Show
              when={tasks().length > 0}
              fallback={
                <div class="px-6 py-12 text-center">
                  <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 mb-4">
                    <span class="text-3xl">✨</span>
                  </div>
                  <p class="text-stone-600 text-lg font-medium mb-2">
                    No tasks for today
                  </p>
                  <p class="text-stone-500 text-sm">Enjoy your free time!</p>
                </div>
              }
            >
              <TaskList tasks={tasks} />
            </Show>
          </div>
        </div>
      </div>

      {/* Motivational quote */}
      <div
        class="mt-12 transition-all duration-1000 delay-500 ease-out"
        style={{
          opacity: mounted() ? 1 : 0,
          transform: mounted() ? "translateY(0)" : "translateY(20px)",
        }}
      >
        <div class="max-w-2xl mx-auto">
          <div class="relative py-8 px-6">
            <div class="absolute left-0 top-0 w-8 h-8 border-l-2 border-t-2 border-amber-300/50" />
            <div class="absolute right-0 bottom-0 w-8 h-8 border-r-2 border-b-2 border-amber-300/50" />
            <p
              class="text-stone-600 text-base md:text-lg italic leading-relaxed text-center"
              style={{
                "font-family": "'Cormorant Garamond', Georgia, serif",
              }}
            >
              "The secret of getting ahead is getting started. The secret of
              getting started is breaking your complex overwhelming tasks into
              small manageable tasks."
            </p>
            <p class="text-stone-400 text-sm text-center mt-4">— Mark Twain</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TodaysTasksView;
