import { Component, For, type JSX } from "solid-js";

interface GenericListProps<T> {
  items: T[];
  renderItem: (item: T) => JSX.Element;
  class?: string;
  onItemClick?: (item: T) => void;
}

export function GenericList<T>(props: GenericListProps<T>) {
  return (
    <div class={props.class ?? ""}>
      <For each={props.items}>
        {(item) => (
          <div
            class="px-5 py-3.5 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer"
            onClick={() => props.onItemClick?.(item)}
          >
            {props.renderItem(item)}
          </div>
        )}
      </For>
    </div>
  );
}

