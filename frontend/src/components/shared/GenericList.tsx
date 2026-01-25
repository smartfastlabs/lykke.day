import { For, type JSX } from "solid-js";

interface GenericListProps<T> {
  items: T[];
  renderItem: (item: T) => JSX.Element;
  class?: string;
  itemClass?: string;
  onItemClick?: (item: T) => void;
}

export function GenericList<T>(props: GenericListProps<T>) {
  const itemClass =
    props.itemClass ??
    "px-5 py-3.5 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer";

  return (
    <div class={props.class ?? ""}>
      <For each={props.items}>
        {(item) => (
          <div
            class={itemClass}
            onClick={() => props.onItemClick?.(item)}
          >
            {props.renderItem(item)}
          </div>
        )}
      </For>
    </div>
  );
}
