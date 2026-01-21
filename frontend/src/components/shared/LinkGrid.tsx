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
    <div class="grid grid-cols-2 p-5 gap-6 max-w-md mx-auto">
      <For each={props.items}>
        {(item) => (
          <button
            onClick={() => onClick(item)}
            class="group p-6 aspect-square flex flex-col items-center justify-center gap-3 bg-white/70 backdrop-blur-md border border-white/70 rounded-2xl shadow-lg shadow-amber-900/5 hover:bg-white/90 hover:shadow-xl hover:shadow-amber-900/10 hover:border-amber-100/80 transition-all duration-200"
          >
            <svg
              viewBox={`0 0 ${item.icon.icon[0]} ${item.icon.icon[1]}`}
              class="w-16 h-16 fill-amber-500/80 group-hover:fill-amber-600 group-hover:scale-110 transition-all duration-200"
            >
              <path d={item.icon.icon[4] as string} />
            </svg>
            <span class="text-sm font-semibold text-stone-700 group-hover:text-stone-800 transition-colors duration-200">
              {item.label}
            </span>
          </button>
        )}
      </For>
    </div>
  );
};

export default LinkGrid;

