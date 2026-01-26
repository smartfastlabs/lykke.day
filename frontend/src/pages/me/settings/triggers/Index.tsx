import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import SettingsPage, { ActionButton } from "@/components/shared/SettingsPage";
import { triggerAPI } from "@/utils/api";
import TriggerList from "@/components/triggers/List";

const TriggersPage: Component = () => {
  const navigate = useNavigate();
  const [triggers] = createResource(triggerAPI.getAll);

  const handleNavigate = (id?: string | null) => {
    if (!id) return;
    navigate(`/me/settings/triggers/${id}`);
  };

  const actionButtons: ActionButton[] = [
    {
      label: "New Trigger",
      icon: faPlus,
      onClick: () => navigate("/me/settings/triggers/new"),
    },
  ];

  return (
    <SettingsPage heading="Triggers" actionButtons={actionButtons}>
      <Show
        when={triggers()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <TriggerList
          triggers={triggers()!}
          onItemClick={(trigger) => handleNavigate(trigger.id)}
        />
      </Show>
    </SettingsPage>
  );
};

export default TriggersPage;
