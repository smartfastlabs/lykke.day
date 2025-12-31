import { Component } from "solid-js";

interface FilterChipProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

export const FilterChip: Component<FilterChipProps> = (props) => (
  <button
    class={`px-2.5 py-1 text-xs rounded-full border transition-all ${
      props.active
        ? "bg-gray-700 text-white border-gray-700"
        : "bg-white text-gray-400 border-gray-200 hover:border-gray-400 hover:text-gray-600"
    }`}
    onClick={props.onClick}
  >
    {props.label}
  </button>
);

