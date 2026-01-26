import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import SettingsPage, { ActionButton } from "@/components/shared/SettingsPage";
import { tacticAPI } from "@/utils/api";
import TacticList from "@/components/tactics/List";

const TacticsPage: Component = () => {
  const navigate = useNavigate();
  const [tactics] = createResource(tacticAPI.getAll);

  const handleNavigate = (id?: string | null) => {
    if (!id) return;
    navigate(`/me/settings/tactics/${id}`);
  };

  const actionButtons: ActionButton[] = [
    {
      label: "New Tactic",
      icon: faPlus,
      onClick: () => navigate("/me/settings/tactics/new"),
    },
  ];

  return (
    <SettingsPage heading="Tactics" actionButtons={actionButtons}>
      <Show
        when={tactics()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <TacticList
          tactics={tactics()!}
          onItemClick={(tactic) => handleNavigate(tactic.id)}
        />
      </Show>
    </SettingsPage>
  );
};

export default TacticsPage;
