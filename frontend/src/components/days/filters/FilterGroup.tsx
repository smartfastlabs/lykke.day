import { Component, type JSX } from "solid-js";

interface FilterGroupProps {
  label: string;
  children: JSX.Element;
}

export const FilterGroup: Component<FilterGroupProps> = (props) => (
  <div class="py-2">
    <div class="text-[10px] uppercase tracking-wider text-gray-400 mb-2">
      {props.label}
    </div>
    <div class="flex flex-wrap gap-1.5">{props.children}</div>
  </div>
);

