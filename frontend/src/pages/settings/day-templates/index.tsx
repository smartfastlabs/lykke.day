import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import Page from "../../../components/shared/layout/page";
import { dayTemplateAPI } from "../../../utils/api";
import { DayTemplate } from "../../../types/api";
import DayTemplateList from "../../../components/dayTemplates/list";

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
          <div class="flex items-center justify-between mb-6">
            <h1 class="text-2xl font-bold">Day Templates</h1>
            <button
              onClick={() => navigate("/settings/day-templates/new")}
              class="px-4 py-2 bg-neutral-900 text-white font-medium rounded-lg hover:bg-neutral-800 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-2 transition-colors"
            >
              New Template
            </button>
          </div>
          <DayTemplateList templates={templates()!} onItemClick={onClick} />
        </div>
      </Show>
    </Page>
  );
};

export default DayTemplatesPage;
