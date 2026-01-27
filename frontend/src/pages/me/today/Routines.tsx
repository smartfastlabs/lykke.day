import {
  Component,
  For,
  Show,
  createMemo,
  createResource,
  createSignal,
} from "solid-js";
import { AnimatedSection } from "@/components/shared/AnimatedSection";
import { SectionCard } from "@/components/shared/SectionCard";
import { StatsCard } from "@/components/shared/StatsCard";
import { FormError } from "@/components/forms";
import { useStreamingData } from "@/providers/streamingData";
import { routineAPI, routineDefinitionAPI } from "@/utils/api";
import type { RoutineDefinition } from "@/types/api";
import RoutineGroupsList, {
  buildRoutineGroups,
} from "@/components/routines/RoutineGroupsList";
import { filterVisibleTasks } from "@/utils/tasks";

export const TodaysRoutinesView: Component = () => {
  const { tasks, routines, sync } = useStreamingData();
  const [addError, setAddError] = createSignal("");
  const [addingId, setAddingId] = createSignal<string | null>(null);

  const [routineDefinitions] = createResource<RoutineDefinition[]>(
    routineDefinitionAPI.getAll,
  );

  const visibleTasks = createMemo(() => filterVisibleTasks(tasks()));
  const routineGroups = createMemo(() =>
    buildRoutineGroups(visibleTasks(), routines()),
  );

  const routineDefinitionIdsForToday = createMemo(() => {
    return new Set(routines().map((routine) => routine.routine_definition_id));
  });

  const stats = createMemo(() => {
    const groups = routineGroups();
    const completed = groups.filter(
      (group) =>
        group.totalCount > 0 && group.completedCount === group.totalCount,
    ).length;
    const punted = groups.filter(
      (group) =>
        group.totalCount > 0 &&
        group.puntedCount === group.totalCount &&
        group.puntedCount > 0,
    ).length;
    const active = groups.filter((group) => group.pendingCount > 0).length;
    return { total: groups.length, completed, active, punted };
  });

  const completionPercentage = createMemo(() => {
    const s = stats();
    return s.total > 0 ? Math.round((s.completed / s.total) * 100) : 0;
  });

  const statItems = createMemo(() => [
    { label: "Total", value: stats().total },
    {
      label: "Active",
      value: stats().active,
      colorClasses:
        "bg-gradient-to-br from-amber-50 to-orange-50 border-amber-100 text-amber-700",
    },
    {
      label: "Done",
      value: stats().completed,
      colorClasses:
        "bg-gradient-to-br from-green-50 to-emerald-50 border-green-100 text-green-700",
    },
    {
      label: "Punted",
      value: stats().punted,
      colorClasses:
        "bg-gradient-to-br from-rose-50 to-red-50 border-rose-200 text-rose-700",
    },
  ]);

  const handleAddRoutine = async (routineDefinitionId?: string | null) => {
    if (!routineDefinitionId) return;
    setAddError("");
    setAddingId(routineDefinitionId);
    try {
      await routineAPI.addToToday(routineDefinitionId);
      sync();
    } catch (error) {
      setAddError(
        error instanceof Error ? error.message : "Failed to add routine.",
      );
    } finally {
      setAddingId(null);
    }
  };

  return (
    <div class="w-full">
      <AnimatedSection delay="200ms">
        <div class="mb-8">
          <StatsCard
            title="Today's Routines"
            completionPercentage={completionPercentage}
            stats={statItems}
          />
        </div>
      </AnimatedSection>

      <AnimatedSection delay="300ms">
        <SectionCard
          title="Add a Routine"
          description="Add tasks from a routine definition to today"
          hasItems={Boolean(routineDefinitions()?.length)}
          emptyState={
            <div class="text-sm text-neutral-500">
              No routine definitions found.
            </div>
          }
        >
          <Show
            when={routineDefinitions()}
            fallback={<div class="text-sm text-neutral-500">Loading...</div>}
          >
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <For each={routineDefinitions() ?? []}>
                {(routineDefinition) => {
                  const isAdded = routineDefinitionIdsForToday().has(
                    routineDefinition.id!,
                  );
                  const isAdding = addingId() === routineDefinition.id;
                  return (
                    <button
                      type="button"
                      class="flex items-center justify-between rounded-md border border-neutral-200 px-3 py-2 text-left hover:border-neutral-300 hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      onClick={() => handleAddRoutine(routineDefinition.id)}
                      disabled={isAdded || isAdding}
                      aria-label={`Add ${routineDefinition.name}`}
                    >
                      <span class="text-sm text-neutral-800">
                        {routineDefinition.name}
                      </span>
                      <span class="text-xs text-neutral-500">
                        {isAdded ? "Added" : isAdding ? "Adding..." : "Add"}
                      </span>
                    </button>
                  );
                }}
              </For>
            </div>
          </Show>
          <FormError error={addError()} />
        </SectionCard>
      </AnimatedSection>

      <AnimatedSection delay="400ms">
        <SectionCard
          title="Your Routines"
          description="Swipe tasks to complete, punt, or snooze"
          hasItems={routineGroups().length > 0}
          emptyState={
            <div class="text-sm text-neutral-500">No routines yet.</div>
          }
        >
          <RoutineGroupsList
            tasks={visibleTasks()}
            routines={routines()}
            expandedByDefault={true}
            isCollapsable={false}
          />
        </SectionCard>
      </AnimatedSection>
    </div>
  );
};

export default TodaysRoutinesView;
