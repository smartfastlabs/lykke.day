import { useNavigate } from "@solidjs/router";
import { Component, For, Show, JSX } from "solid-js";
import { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import Page from "@/components/shared/layout/Page";

export interface ActionButton {
  label: string;
  icon?: IconDefinition;
  onClick: () => void;
}

interface SettingsPageProps {
  heading: string;
  actionButtons?: ActionButton[];
  children: JSX.Element;
  bottomLink?: {
    label: string;
    url: string;
  };
}

const SettingsPage: Component<SettingsPageProps> = (props) => {
  const navigate = useNavigate();

  return (
    <Page>
      <div class="w-full px-5 py-4 flex-1 flex flex-col">
        {/* Heading */}
        <h1 class="text-2xl font-bold mb-6">{props.heading}</h1>

        {/* Optional Action Buttons */}
        <Show when={props.actionButtons && props.actionButtons.length > 0}>
          <div class="flex flex-row gap-3 mb-6">
            <For each={props.actionButtons}>
              {(button) => (
                <button
                  onClick={button.onClick}
                  class="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg text-gray-600 hover:bg-gray-200 hover:text-gray-800 transition-colors duration-150"
                >
                  <Show when={button.icon}>
                    {(icon) => (
                      <svg
                        viewBox={`0 0 ${icon().icon[0]} ${icon().icon[1]}`}
                        class="w-4 h-4 fill-gray-400"
                      >
                        <path d={icon().icon[4] as string} />
                      </svg>
                    )}
                  </Show>
                  <span class="text-sm font-medium">{button.label}</span>
                </button>
              )}
            </For>
          </div>
        </Show>

        {/* Body */}
        <div class="flex-1">{props.children}</div>

        {/* Optional Bottom Link */}
        <Show when={props.bottomLink}>
          {(link) => (
            <div class="mt-6 pt-6 border-t border-gray-200">
              <button
                onClick={() => navigate(link().url)}
                class="text-sm text-gray-600 hover:text-gray-800 transition-colors"
              >
                {link().label}
              </button>
            </div>
          )}
        </Show>
      </div>
    </Page>
  );
};

export default SettingsPage;

