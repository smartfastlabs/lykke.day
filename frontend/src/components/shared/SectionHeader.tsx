import { Component } from "solid-js";

interface SectionHeaderProps {
  label: string;
}

export const SectionHeader: Component<SectionHeaderProps> = (props) => (
  <div class="px-0 py-2">
    <span class="text-xs uppercase tracking-[0.25em] text-amber-600/80">
      {props.label}
    </span>
  </div>
);

