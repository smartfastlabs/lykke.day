import { Component, type JSX, Show, createMemo, createSignal } from "solid-js";
import { GenericList } from "@/components/shared/GenericList";
import { fuzzyMatch } from "@/utils/search";

interface SettingsListProps<T> {
  items: T[];
  getItemLabel: (item: T) => string;
  renderItem: (item: T) => JSX.Element;
  onItemClick?: (item: T) => void;
  searchPlaceholder?: string;
  emptyStateLabel?: string;
}

const SettingsList = <T,>(props: SettingsListProps<T>) => {
  const [query, setQuery] = createSignal("");

  const filteredItems = createMemo(() => {
    const searchValue = query().trim();
    if (!searchValue) return props.items;
    return props.items.filter((item) =>
      fuzzyMatch(searchValue, props.getItemLabel(item))
    );
  });

  const emptyLabel = () =>
    props.emptyStateLabel ?? "Nothing here yet.";

  const hasItems = () => props.items.length > 0;
  const hasResults = () => filteredItems().length > 0;

  return (
    <div class="space-y-4">
      <div class="relative">
        <input
          type="search"
          value={query()}
          onInput={(event) => setQuery(event.currentTarget.value)}
          placeholder={props.searchPlaceholder ?? "Search by name..."}
          class="w-full rounded-2xl border border-amber-100/80 bg-white/80 px-4 py-3 text-sm text-stone-700 placeholder-stone-400 shadow-sm shadow-amber-900/5 focus:border-amber-200 focus:outline-none focus:ring-2 focus:ring-amber-200/70"
        />
      </div>

      <Show
        when={hasItems() && hasResults()}
        fallback={
          <div class="rounded-2xl border border-amber-100/70 bg-white/70 px-4 py-6 text-center text-sm text-stone-500 shadow-sm shadow-amber-900/5">
            {hasItems()
              ? `No matches for "${query()}".`
              : emptyLabel()}
          </div>
        }
      >
        <GenericList
          items={filteredItems()}
          renderItem={props.renderItem}
          onItemClick={props.onItemClick}
          class="overflow-hidden rounded-2xl border border-amber-100/80 bg-white/80 shadow-sm shadow-amber-900/5 divide-y divide-amber-100/60"
          itemClass="px-5 py-4 hover:bg-amber-50/70 transition-colors cursor-pointer"
        />
      </Show>
    </div>
  );
};

export default SettingsList;
