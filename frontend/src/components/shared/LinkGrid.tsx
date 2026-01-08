import { useNavigate } from "@solidjs/router";
import { Component, For } from "solid-js";
import { IconDefinition } from "@fortawesome/fontawesome-svg-core";

export interface LinkItem {
  label: string;
  icon: IconDefinition;
  url?: string;
  method?: CallableFunction;
}

interface LinkGridProps {
  items: LinkItem[];
}

const LinkGrid: Component<LinkGridProps> = (props) => {
  const navigate = useNavigate();

  function onClick(item: LinkItem) {
    if (item.url) {
      return navigate(item.url);
    }
    if (item.method) {
      return item.method();
    }
  }

  return (
    <div class="grid grid-cols-2 p-5 gap-10 max-w-md mx-auto">
      <For each={props.items}>
        {(item) => (
          <button
            onClick={() => onClick(item)}
            class="p-4 aspect-square flex flex-col items-center justify-center gap-2 bg-gray-100 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-600 transition-colors duration-150"
          >
            <svg
              viewBox={`0 0 ${item.icon.icon[0]} ${item.icon.icon[1]}`}
              class="w-18 h-18 fill-gray-400"
            >
              <path d={item.icon.icon[4] as string} />
            </svg>
            <span class="text-sm font-medium">{item.label}</span>
          </button>
        )}
      </For>
    </div>
  );
};

export default LinkGrid;

