import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import SettingsPage, { ActionButton } from "@/components/shared/SettingsPage";
import { dayTemplateAPI } from "@/utils/api";
import { DayTemplate } from "@/types/api";
import DayTemplateList from "@/components/dayTemplates/List";

const DayTemplatesPage: Component = () => {
  const navigate = useNavigate();
  const [templates] = createResource(dayTemplateAPI.getAll);

  const onClick = (template: DayTemplate) => {
    if (template.id) {
      navigate(`/me/settings/day-templates/${template.id}`);
    }
  };

  const actionButtons: ActionButton[] = [
    {
      label: "New Template",
      icon: faPlus,
      onClick: () => navigate("/me/settings/day-templates/new"),
    },
  ];

  return (
    <SettingsPage heading="Day Templates" actionButtons={actionButtons}>
      <Show
        when={templates()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <DayTemplateList templates={templates()!} onItemClick={onClick} />
      </Show>
    </SettingsPage>
  );
};

export default DayTemplatesPage;
