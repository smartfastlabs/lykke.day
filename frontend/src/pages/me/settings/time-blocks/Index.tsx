import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import SettingsPage, { ActionButton } from "@/components/shared/SettingsPage";
import { timeBlockDefinitionAPI } from "@/utils/api";
import TimeBlockDefinitionList from "@/components/time-blocks/List";

const TimeBlocksPage: Component = () => {
  const navigate = useNavigate();
  const [timeBlockDefinitions] = createResource(timeBlockDefinitionAPI.getAll);

  const handleNavigate = (id?: string | null) => {
    if (!id) return;
    navigate(`/me/settings/time-blocks/${id}`);
  };

  const actionButtons: ActionButton[] = [
    {
      label: "New Time Block",
      icon: faPlus,
      onClick: () => navigate("/me/settings/time-blocks/new"),
    },
  ];

  return (
    <SettingsPage heading="Time Blocks" actionButtons={actionButtons}>
      <Show
        when={timeBlockDefinitions()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <TimeBlockDefinitionList
          timeBlockDefinitions={timeBlockDefinitions()!}
          onItemClick={(timeBlockDefinition) => handleNavigate(timeBlockDefinition.id)}
        />
      </Show>
    </SettingsPage>
  );
};

export default TimeBlocksPage;

