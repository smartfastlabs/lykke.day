import { Component } from "solid-js";

interface SectionHeaderProps {
  label: string;
}

export const SectionHeader: Component<SectionHeaderProps> = (props) => (
  <div class="px-5 py-2 bg-gray-50 border-b border-gray-200">
    <span class="text-xs uppercase tracking-wider text-gray-400">
      {props.label}
    </span>
  </div>
);

