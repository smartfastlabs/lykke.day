import { Component, JSX, Show } from "solid-js";

interface SectionCardProps {
  title: string;
  description?: string;
  emptyState?: JSX.Element;
  hasItems: boolean;
  children: JSX.Element;
}

export const SectionCard: Component<SectionCardProps> = (props) => {
  return (
    <div class="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl shadow-xl shadow-amber-900/5 overflow-hidden">
      <div class="px-6 py-5 border-b border-stone-100">
        <h2 class="text-xl md:text-2xl font-semibold text-stone-800">
          {props.title}
        </h2>
        <Show when={props.description}>
          <p class="text-sm text-stone-500 mt-1">{props.description}</p>
        </Show>
      </div>

      <div class="p-4">
        <Show when={props.hasItems} fallback={props.emptyState}>
          {props.children}
        </Show>
      </div>
    </div>
  );
};
