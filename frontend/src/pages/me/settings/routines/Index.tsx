import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import SettingsPage, { ActionButton } from "@/components/shared/SettingsPage";
import { routineDefinitionAPI } from "@/utils/api";
import RoutineList from "@/components/routines/List";

const RoutineDefinitionsPage: Component = () => {
  const navigate = useNavigate();
  const [routineDefinitions] = createResource(routineDefinitionAPI.getAll);

  const handleNavigate = (id?: string | null) => {
    if (!id) return;
    navigate(`/me/settings/routine-definitions/${id}`);
  };

  const actionButtons: ActionButton[] = [
    {
      label: "New Routine Definition",
      icon: faPlus,
      onClick: () => navigate("/me/settings/routine-definitions/new"),
    },
  ];

  return (
    <SettingsPage heading="Routine Definitions" actionButtons={actionButtons}>
      <Show
        when={routineDefinitions()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <RoutineList
          routineDefinitions={routineDefinitions()!}
          onItemClick={(routineDefinition) =>
            handleNavigate(routineDefinition.id)
          }
        />
      </Show>
    </SettingsPage>
  );
};

export default RoutineDefinitionsPage;
