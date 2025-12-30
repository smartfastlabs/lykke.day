import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import Page from "../../components/shared/layout/page";
import { dayTemplateAPI } from "../../utils/api";
import { DayTemplate } from "../../types/api";
import DayTemplateList from "../../components/dayTemplates/list";

const DayTemplatesPage: Component = () => {
  const navigate = useNavigate();
  const [templates] = createResource(dayTemplateAPI.getAll);

  const onClick = (template: DayTemplate) => {
    if (template.uuid) {
      navigate(`/settings/day-templates/${template.uuid}`);
    }
  };

  return (
    <Page>
      <Show
        when={templates()}
        fallback={<div class="text-center text-gray-500">Loading...</div>}
      >
        <div class="max-w-2xl mx-auto p-4">
          <h1 class="text-2xl font-bold mb-6">Day Templates</h1>
          <DayTemplateList templates={templates()!} onItemClick={onClick} />
        </div>
      </Show>
    </Page>
  );
};

export default DayTemplatesPage;
