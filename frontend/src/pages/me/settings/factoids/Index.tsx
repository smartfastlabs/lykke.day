import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import SettingsPage, { ActionButton } from "@/components/shared/SettingsPage";
import { factoidAPI } from "@/utils/api";
import { Factoid } from "@/types/api";
import FactoidList from "@/components/factoids/List";

const FactoidsPage: Component = () => {
  const navigate = useNavigate();
  const [factoids] = createResource(factoidAPI.getAll);

  const onClick = (factoid: Factoid) => {
    if (factoid.id) {
      navigate(`/me/settings/factoids/${factoid.id}`);
    }
  };

  const actionButtons: ActionButton[] = [
    {
      label: "New Factoid",
      icon: faPlus,
      onClick: () => navigate("/me/settings/factoids/new"),
    },
  ];

  return (
    <SettingsPage heading="Factoids" actionButtons={actionButtons}>
      <Show
        when={factoids()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <FactoidList factoids={factoids()!} onItemClick={onClick} />
      </Show>
    </SettingsPage>
  );
};

export default FactoidsPage;
