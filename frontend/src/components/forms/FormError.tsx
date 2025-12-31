import { Component, Show } from "solid-js";

interface FormErrorProps {
  error?: string;
}

export const FormError: Component<FormErrorProps> = (props) => (
  <Show when={props.error}>
    <p class="text-sm text-red-600 text-center">{props.error}</p>
  </Show>
);

