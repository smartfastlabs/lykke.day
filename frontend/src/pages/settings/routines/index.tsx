import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import Page from "@/components/shared/layout/page";
import { routineAPI } from "@/utils/api";
import RoutineList from "@/components/routines/list";
import { Icon } from "@/components/shared/icon";

const RoutinesPage: Component = () => {
  const navigate = useNavigate();
  const [routines] = createResource(routineAPI.getAll);

  const handleNavigate = (id?: string) => {
    if (!id) return;
    navigate(`/settings/routines/${id}`);
  };

  return (
    <Page>
      <Show
        when={routines()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <div class="w-full px-5 py-4">
          <div class="flex items-center justify-between mb-6">
            <h1 class="text-2xl font-bold">Routines</h1>
            <button
              onClick={() => navigate("/settings/routines/new")}
              class="flex items-center justify-center w-8 h-8 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="New Routine"
            >
              <Icon key="plus" class="w-5 h-5" />
            </button>
          </div>
          <RoutineList
            routines={routines()!}
            onItemClick={(routine) => handleNavigate(routine.id)}
          />
        </div>
      </Show>
    </Page>
  );
};

export default RoutinesPage;
