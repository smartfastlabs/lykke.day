import { useNavigate } from "@solidjs/router";
import { Component, For, Show, createResource } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import { templateAPI } from "@/utils/api";
import type { SystemTemplate } from "@/types/api";

const PromptsSettingsPage: Component = () => {
  const navigate = useNavigate();
  const [templates] = createResource<SystemTemplate[]>(
    templateAPI.getSystemTemplates
  );

  const handleClick = (usecase: string) => {
    navigate(`/me/settings/prompts/detail?usecase=${encodeURIComponent(usecase)}`);
  };

  return (
    <SettingsPage heading="Prompt Templates">
      <Show
        when={templates()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <div class="space-y-3">
          <For each={templates()!}>
            {(template) => {
              const overriddenCount = template.parts.filter(
                (part) => part.has_user_override
              ).length;
              const totalParts = template.parts.length;
              const statusLabel =
                overriddenCount > 0
                  ? `Customized (${overriddenCount}/${totalParts})`
                  : "Default";
              return (
              <button
                type="button"
                onClick={() => handleClick(template.usecase)}
                class="w-full flex items-center justify-between px-4 py-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div class="text-left">
                  <div class="font-medium text-gray-900">{template.name}</div>
                  <div class="text-sm text-gray-500">{template.usecase}</div>
                </div>
                <div class="text-xs px-2 py-1 rounded-full border border-gray-300 text-gray-600">
                  {statusLabel}
                </div>
              </button>
              );
            }}
          </For>
        </div>
      </Show>
    </SettingsPage>
  );
};

export default PromptsSettingsPage;
