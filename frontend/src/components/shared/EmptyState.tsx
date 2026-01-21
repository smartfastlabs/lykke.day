import { Component } from "solid-js";

interface EmptyStateProps {
  message?: string;
}

export const EmptyState: Component<EmptyStateProps> = (props) => (
  <div class="px-5 py-16 text-center">
    <p class="text-sm text-gray-400">{props.message ?? "Nothing scheduled"}</p>
  </div>
);

