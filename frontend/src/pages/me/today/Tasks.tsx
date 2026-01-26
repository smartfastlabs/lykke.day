import { Component, createMemo, createSignal, onCleanup, onMount } from "solid-js";
import { useStreamingData } from "@/providers/streamingData";
import TaskList from "@/components/tasks/List";
import { Task, TaskCategory } from "@/types/api";
import { AnimatedSection } from "@/components/shared/AnimatedSection";
import { StatsCard } from "@/components/shared/StatsCard";
import { SectionCard } from "@/components/shared/SectionCard";
import { MotivationalQuote } from "@/components/shared/MotivationalQuote";
import { FormError, Input, Select, SubmitButton } from "@/components/forms";
import { ALL_TASK_CATEGORIES } from "@/types/api/constants";
import { filterVisibleTasks } from "@/utils/tasks";

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
  const [now, setNow] = createSignal(new Date());

  onMount(() => {
    const interval = setInterval(() => {
      setNow(new Date());
    }, 30000);

    onCleanup(() => {
      clearInterval(interval);
    });
  });

  const visibleTasks = createMemo(() => filterVisibleTasks(tasks(), now()));
  const stats = createMemo(() => getTaskStats(visibleTasks()));
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
      setFormError(error instanceof Error ? error.message : "Failed to add task.");
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
          description="Swipe right to complete, left to punt or snooze"
          hasItems={visibleTasks().length > 0}
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
          <TaskList tasks={visibleTasks} />
        </SectionCard>
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
