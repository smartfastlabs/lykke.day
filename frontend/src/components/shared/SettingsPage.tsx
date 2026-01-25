import { useNavigate } from "@solidjs/router";
import { Component, For, Show, JSX } from "solid-js";
import { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { faPlus } from "@fortawesome/free-solid-svg-icons";

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
    <div class="w-full flex-1 flex flex-col gap-6">
      {/* Heading */}
      <div class="flex flex-row items-center justify-between gap-3">
        <h1 class="text-2xl md:text-3xl font-semibold text-stone-800">
          {props.heading}
        </h1>
        <Show when={props.actionButtons && props.actionButtons.length > 0}>
          <div class="flex flex-wrap gap-2">
            <For each={props.actionButtons}>
              {(button) => (
                <Show
                  when={button.icon === faPlus && button.label.startsWith("New")}
                  fallback={
                    <button
                      onClick={button.onClick}
                      class="inline-flex items-center gap-2 rounded-full border border-amber-100/80 bg-white/80 px-4 py-2 text-sm font-semibold text-amber-700 shadow-sm shadow-amber-900/5 transition hover:border-amber-200 hover:bg-white"
                    >
                      <Show when={button.icon}>
                        {(icon) => (
                          <svg
                            viewBox={`0 0 ${icon().icon[0]} ${icon().icon[1]}`}
                            class="h-4 w-4 fill-amber-600/80"
                          >
                            <path d={icon().icon[4] as string} />
                          </svg>
                        )}
                      </Show>
                      <span>{button.label}</span>
                    </button>
                  }
                >
                  <button
                    onClick={button.onClick}
                    class="inline-flex items-center justify-center w-9 h-9 rounded-full border border-amber-100/80 bg-amber-50/70 text-amber-600/80 transition hover:bg-amber-100/80 hover:text-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200"
                    aria-label={button.label}
                    title={button.label}
                  >
                    <svg
                      viewBox={`0 0 ${faPlus.icon[0]} ${faPlus.icon[1]}`}
                      class="h-4 w-4 fill-amber-600/80"
                    >
                      <path d={faPlus.icon[4] as string} />
                    </svg>
                  </button>
                </Show>
              )}
            </For>
          </div>
        </Show>
      </div>

      {/* Body */}
      <div class="flex-1">{props.children}</div>

      {/* Optional Bottom Link */}
      <Show when={props.bottomLink}>
        {(link) => (
          <div class="pt-4 border-t border-amber-100/80">
            <button
              onClick={() => navigate(link().url)}
              class="text-sm font-medium text-amber-700 hover:text-amber-800 transition-colors"
            >
              {link().label}
            </button>
          </div>
        )}
      </Show>
    </div>
  );
};

export default SettingsPage;

