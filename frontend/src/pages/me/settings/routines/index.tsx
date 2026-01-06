import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import SettingsPage, { ActionButton } from "@/components/shared/settingsPage";
import { routineAPI } from "@/utils/api";
import RoutineList from "@/components/routines/list";

const RoutinesPage: Component = () => {
  const navigate = useNavigate();
  const [routines] = createResource(routineAPI.getAll);

  const handleNavigate = (id?: string) => {
    if (!id) return;
    navigate(`/me/settings/routines/${id}`);
  };

  const actionButtons: ActionButton[] = [
    {
      label: "New Routine",
      icon: faPlus,
      onClick: () => navigate("/me/settings/routines/new"),
    },
  ];

  return (
    <SettingsPage heading="Routines" actionButtons={actionButtons}>
      <Show
        when={routines()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <RoutineList
          routines={routines()!}
          onItemClick={(routine) => handleNavigate(routine.id)}
        />
      </Show>
    </SettingsPage>
  );
};

export default RoutinesPage;
