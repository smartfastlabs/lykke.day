import { Component, type JSX } from "solid-js";

interface ButtonProps {
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  onClick?: () => void;
  variant?: "primary" | "secondary";
  children: JSX.Element;
}

export const Button: Component<ButtonProps> = (props) => {
  const baseClass =
    "w-full py-3 px-4 font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors";

  const variantClass = () =>
    props.variant === "secondary"
      ? "bg-neutral-100 text-neutral-900 hover:bg-neutral-200 focus:ring-neutral-500"
      : "bg-neutral-900 text-white hover:bg-neutral-800 focus:ring-neutral-900";

  return (
    <button
      type={props.type ?? "button"}
      disabled={props.disabled}
      onClick={() => props.onClick?.()}
      class={`${baseClass} ${variantClass()}`}
    >
      {props.children}
    </button>
  );
};

interface SubmitButtonProps {
  isLoading?: boolean;
  loadingText?: string;
  text: string;
}

export const SubmitButton: Component<SubmitButtonProps> = (props) => (
  <Button type="submit" disabled={props.isLoading}>
    {props.isLoading ? (props.loadingText ?? "Loading...") : props.text}
  </Button>
);
