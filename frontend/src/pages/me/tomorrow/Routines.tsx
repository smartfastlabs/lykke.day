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
import { FormError } from "@/components/forms";
import { routineAPI, routineDefinitionAPI, tomorrowAPI } from "@/utils/api";
import type { RoutineDefinition } from "@/types/api";
import { useTomorrowData } from "@/pages/me/tomorrow/useTomorrowData";

export const TomorrowRoutinesView: Component = () => {
  const { routines, refetchAll } = useTomorrowData();
  const [addError, setAddError] = createSignal("");
  const [addingId, setAddingId] = createSignal<string | null>(null);

  const [routineDefinitions] = createResource<RoutineDefinition[]>(
    routineDefinitionAPI.getAll,
  );

  const routineDefinitionIdsForTomorrow = createMemo(() => {
    return new Set(routines().map((routine) => routine.routine_definition_id));
  });

  const handleAddRoutine = async (routineDefinitionId?: string | null) => {
    if (!routineDefinitionId) return;
    setAddError("");
    setAddingId(routineDefinitionId);
    try {
      // Ensure tomorrow exists before adding routine tasks
      await tomorrowAPI.ensureScheduled();
      await routineAPI.addToTomorrow(routineDefinitionId);
      refetchAll();
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
        <SectionCard
          title="Add a Routine"
          description="Add tasks from a routine definition to tomorrow"
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
                  const isAdded = routineDefinitionIdsForTomorrow().has(
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
    </div>
  );
};

export default TomorrowRoutinesView;
