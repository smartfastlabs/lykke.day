import { useNavigate } from "@solidjs/router";
import { Component, For, createResource } from "solid-js";
import { template } from "solid-js/web";

import { dayAPI } from "../../../utils/api";
import Page from "../../shared/layout/page";
import { getIcon } from "../../../utils/icons";

const DayTemplatePage: Component = () => {
  const [templates] = createResource(dayAPI.getTemplates);

  const onClick = async (template) => {
    console.log(template);
  }

  return (
    <Page>
      <div class="grid grid-cols-2 gap-10 max-w-md mx-auto">
        <For each={templates()}>
          {(template) => {
            const icon = getIcon(template.icon);
            return (
                <button
                onClick={onClick}
                class="aspect-square flex flex-col items-center justify-center gap-2 bg-gray-100 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-600 transition-colors duration-150"
                >
                <svg
                    viewBox={`0 0 ${icon.icon[0]} ${icon.icon[1]}`}
                    class="w-18 h-18 fill-gray-400"
                >
                    <path d={icon.icon[4] as string} />
                </svg>
                <span class="text-sm font-medium">{template.name}</span>
                </button>
            )
        }}
        </For>
      </div>
    </Page>
  );
};

export default DayTemplatePage;