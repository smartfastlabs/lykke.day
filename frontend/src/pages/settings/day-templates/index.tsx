import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import Page from "../../../components/shared/layout/page";
import { dayTemplateAPI } from "../../../utils/api";
import { DayTemplate } from "../../../types/api";
import DayTemplateList from "../../../components/dayTemplates/list";
import { Icon } from "../../../components/shared/icon";

const DayTemplatesPage: Component = () => {
  const navigate = useNavigate();
  const [templates] = createResource(dayTemplateAPI.getAll);

  const onClick = (template: DayTemplate) => {
    if (template.id) {
      navigate(`/settings/day-templates/${template.id}`);
    }
  };

  return (
    <Page>
      <Show
        when={templates()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <div class="w-full px-5 py-4">
          <div class="flex items-center justify-between mb-6">
            <h1 class="text-2xl font-bold">Day Templates</h1>
            <button
              onClick={() => navigate("/settings/day-templates/new")}
              class="flex items-center justify-center w-8 h-8 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="New Template"
            >
              <Icon key="plus" class="w-5 h-5" />
            </button>
          </div>
          <DayTemplateList templates={templates()!} onItemClick={onClick} />
        </div>
      </Show>
    </Page>
  );
};

export default DayTemplatesPage;
