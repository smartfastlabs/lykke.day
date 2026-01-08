import { useNavigate } from "@solidjs/router";
import { Component, For, createResource } from "solid-js";
import { template } from "solid-js/web";

import { dayAPI } from "@/utils/api";
import { getIcon } from "@/utils/icons";
import { DayTemplate } from "@/types/api";

const DayTemplatePage: Component = () => {
  const [templates] = createResource(dayAPI.getTemplates);

  const onClick = async (template: DayTemplate) => {
    console.log(template);
  };

  return (
    <div class="grid grid-cols-2 gap-10 max-w-md mx-auto">
      <For each={templates()}>
        {(template) => {
          const iconName = template.icon || "default";
          const icon = getIcon(iconName);
          if (!icon) return null;
          return (
            <button
              onClick={() => onClick(template)}
              class="aspect-square flex flex-col items-center justify-center gap-2 bg-gray-100 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-600 transition-colors duration-150"
            >
              <svg
                viewBox={`0 0 ${icon.icon[0]} ${icon.icon[1]}`}
                class="w-18 h-18 fill-gray-400"
              >
                <path d={String(icon.icon[4])} />
              </svg>
              <span class="text-sm font-medium">{template.slug}</span>
            </button>
          );
        }}
      </For>
    </div>
  );
};

export default DayTemplatePage;
