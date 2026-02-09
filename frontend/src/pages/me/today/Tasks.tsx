import { Component, Show, createMemo, createSignal } from "solid-js";
import { useStreamingData } from "@/providers/streamingData";
import TaskList from "@/components/tasks/List";
import { Task, TaskCategory } from "@/types/api";
import { AnimatedSection } from "@/components/shared/AnimatedSection";
import { StatsCard } from "@/components/shared/StatsCard";
import { SectionCard } from "@/components/shared/SectionCard";
import { MotivationalQuote } from "@/components/shared/MotivationalQuote";
import { FormError, Input, Select, SubmitButton } from "@/components/forms";
import { ALL_TASK_CATEGORIES } from "@/types/api/constants";

const getTaskStats = (tasks: Task[]) => {
  const total = tasks.length;
  const completed = tasks.filter((t) => t.status === "COMPLETE").length;
  const pending = tasks.filter((t) => t.status === "PENDING").length;
  const punted = tasks.filter((t) => t.status === "PUNT").length;
  return { total, completed, pending, punted };
};

export const TodaysTasksView: Component = () => {
  const { tasks, addAdhocTask, day } = useStreamingData();
  const [taskName, setTaskName] = createSignal("");
  const [taskCategory, setTaskCategory] = createSignal<TaskCategory>("WORK");
  const [isSaving, setIsSaving] = createSignal(false);
  const [formError, setFormError] = createSignal("");
  const [showDone, setShowDone] = createSignal(false);
  const [showPunted, setShowPunted] = createSignal(false);

  // IMPORTANT: this is the "all tasks" view, so we intentionally do NOT filter
  // out tasks with `timing_status === "hidden"` (which the backend uses for
  // things like "later today" or snoozed items).
  const allTasks = createMemo(() => tasks() ?? []);
  const activeTasks = createMemo(() =>
    allTasks().filter(
<<<<<<< Updated upstream
      (task) => task.status !== "COMPLETE" && task.status !== "PUNT",
    ),
  );
  const completedTasks = createMemo(() =>
    allTasks().filter((task) => task.status === "COMPLETE"),
  );
  const puntedTasks = createMemo(() =>
    allTasks().filter((task) => task.status === "PUNT"),
=======
      (task) => task.status !== "COMPLETE" && task.status !== "PUNT"
    )
  );
  const completedTasks = createMemo(() =>
    allTasks().filter((task) => task.status === "COMPLETE")
  );
  const puntedTasks = createMemo(() =>
    allTasks().filter((task) => task.status === "PUNT")
>>>>>>> Stashed changes
  );
  const stats = createMemo(() => getTaskStats(allTasks()));
  const completionPercentage = createMemo(() => {
    const s = stats();
    return s.total > 0 ? Math.round((s.completed / s.total) * 100) : 0;
  });

  const statItems = createMemo(() => [
    { label: "Total", value: stats().total },
    {
      label: "Done",
      value: stats().completed,
      colorClasses:
        "bg-gradient-to-br from-green-50 to-emerald-50 border-green-100 text-green-700",
    },
    {
      label: "Pending",
      value: stats().pending,
      colorClasses:
        "bg-gradient-to-br from-amber-50 to-orange-50 border-amber-100 text-amber-700",
    },
    {
      label: "Punted",
      value: stats().punted,
      colorClasses:
        "bg-gradient-to-br from-rose-50 to-red-50 border-rose-200 text-rose-700",
    },
  ]);

  const emptyState = <></>;

  const handleAddTask = async (event: Event) => {
    event.preventDefault();
    setFormError("");
    const name = taskName().trim();
    if (!name) {
      setFormError("Task name is required.");
      return;
    }
    if (!day()?.date) {
      setFormError("Day context not loaded yet.");
      return;
    }
    try {
      setIsSaving(true);
      await addAdhocTask(name, taskCategory());
      setTaskName("");
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Failed to add task."
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div class="w-full">
      <AnimatedSection delay="200ms">
        <div class="mb-8">
          <StatsCard
            title="Today's Progress"
            completionPercentage={completionPercentage}
            stats={statItems}
          />
        </div>
      </AnimatedSection>

      <AnimatedSection delay="300ms">
        <SectionCard
          title="Your Tasks"
          description="Swipe right to complete, left to punt or snooze. Done & punted tasks are tucked below."
          hasItems={activeTasks().length > 0}
          emptyState={emptyState}
        >
          <form class="mb-6 space-y-3" onSubmit={handleAddTask}>
            <div class="grid gap-3 md:grid-cols-[2fr_1fr_auto] md:items-center">
              <Input
                id="adhoc-task-name"
                placeholder="Add a task"
                value={taskName}
                onChange={setTaskName}
                required
              />
              <Select
                id="adhoc-task-category"
                placeholder="Category"
                value={taskCategory}
                onChange={(value) => setTaskCategory(value)}
                options={ALL_TASK_CATEGORIES}
                required
              />
              <div class="md:min-w-[140px]">
                <SubmitButton
                  isLoading={isSaving()}
                  loadingText="Adding..."
                  text="Add task"
                />
              </div>
            </div>
            <FormError error={formError()} />
          </form>
          <TaskList tasks={activeTasks} />
        </SectionCard>
      </AnimatedSection>

      <AnimatedSection delay="400ms">
        <Show when={completedTasks().length > 0 || puntedTasks().length > 0}>
          <div class="mt-6 space-y-3">
            <Show when={completedTasks().length > 0}>
              <details
                class="bg-white/40 backdrop-blur-md border border-white/70 rounded-2xl shadow-sm shadow-amber-900/5 overflow-hidden"
                open={showDone()}
                onToggle={(e) => {
                  const target = e.currentTarget as unknown as { open: boolean };
                  setShowDone(target.open);
                }}
              >
                <summary class="cursor-pointer select-none px-6 py-4 flex items-center justify-between list-none [&::-webkit-details-marker]:hidden">
                  <div class="flex items-baseline gap-2">
                    <span class="text-sm font-medium text-stone-700">Done</span>
                    <span class="text-xs text-stone-400">
                      ({completedTasks().length})
                    </span>
                  </div>
                  <span class="text-xs text-stone-400">
                    {showDone() ? "Hide" : "Show"}
                  </span>
                </summary>
                <div class="px-4 pb-4">
                  <TaskList tasks={completedTasks} interactive={false} />
                </div>
              </details>
            </Show>

            <Show when={puntedTasks().length > 0}>
              <details
                class="bg-white/40 backdrop-blur-md border border-white/70 rounded-2xl shadow-sm shadow-amber-900/5 overflow-hidden"
                open={showPunted()}
                onToggle={(e) => {
                  const target = e.currentTarget as unknown as { open: boolean };
                  setShowPunted(target.open);
                }}
              >
                <summary class="cursor-pointer select-none px-6 py-4 flex items-center justify-between list-none [&::-webkit-details-marker]:hidden">
                  <div class="flex items-baseline gap-2">
                    <span class="text-sm font-medium text-stone-700">
                      Punted
                    </span>
                    <span class="text-xs text-stone-400">
                      ({puntedTasks().length})
                    </span>
                  </div>
                  <span class="text-xs text-stone-400">
                    {showPunted() ? "Hide" : "Show"}
                  </span>
                </summary>
                <div class="px-4 pb-4">
                  <TaskList tasks={puntedTasks} interactive={false} />
                </div>
              </details>
            </Show>
          </div>
        </Show>
      </AnimatedSection>

      <AnimatedSection delay="500ms">
        <MotivationalQuote
          quote="The secret of getting ahead is getting started. The secret of getting started is breaking your complex overwhelming tasks into small manageable tasks."
          author="Mark Twain"
        />
      </AnimatedSection>
    </div>
  );
};

export default TodaysTasksView;
