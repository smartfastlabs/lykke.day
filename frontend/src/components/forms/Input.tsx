import { Component, type Accessor } from "solid-js";

// Shared input styles
const inputClass =
  "w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow";

interface InputProps {
  id: string;
  type?: "text" | "email" | "password" | "number" | "time" | "tel";
  inputMode?:
    | "none"
    | "text"
    | "search"
    | "url"
    | "email"
    | "tel"
    | "decimal"
    | "numeric";
  placeholder: string;
  value: Accessor<string>;
  onChange: (value: string) => void;
  required?: boolean;
  autocomplete?: string;
  min?: string;
  max?: string;
  maxLength?: number;
  pattern?: string;
}

export const Input: Component<InputProps> = (props) => (
  <div>
    <label for={props.id} class="sr-only">
      {props.placeholder}
    </label>
    <input
      id={props.id}
      type={props.type ?? "text"}
      inputmode={props.inputMode}
      placeholder={props.placeholder}
      value={props.value()}
      onInput={(e) => props.onChange(e.currentTarget.value)}
      class={inputClass}
      required={props.required}
      autocomplete={props.autocomplete}
      min={props.min}
      max={props.max}
      maxLength={props.maxLength}
      pattern={props.pattern}
    />
  </div>
);

interface TextAreaProps {
  id: string;
  placeholder: string;
  value: Accessor<string>;
  onChange: (value: string) => void;
  rows?: number;
  required?: boolean;
}

export const TextArea: Component<TextAreaProps> = (props) => (
  <div>
    <label for={props.id} class="sr-only">
      {props.placeholder}
    </label>
    <textarea
      id={props.id}
      placeholder={props.placeholder}
      value={props.value()}
      onInput={(e) => props.onChange(e.currentTarget.value)}
      class={inputClass}
      rows={props.rows ?? 3}
      required={props.required}
    />
  </div>
);

type SelectOption<T extends string> = T | { value: T; label: string };

interface SelectProps<T extends string> {
  id: string;
  value: Accessor<T>;
  onChange: (value: T) => void;
  options: SelectOption<T>[];
  required?: boolean;
  placeholder?: string;
}

export function Select<T extends string>(props: SelectProps<T>) {
  return (
    <div>
      <label for={props.id} class="sr-only">
        {props.placeholder ?? props.id}
      </label>
      <select
        id={props.id}
        value={props.value()}
        onChange={(e) => props.onChange(e.currentTarget.value as T)}
        class={inputClass}
        required={props.required}
      >
        {props.placeholder && <option value="">{props.placeholder}</option>}
        {props.options.map((option) => {
          if (typeof option === "string") {
            return <option value={option}>{option}</option>;
          }
          return <option value={option.value}>{option.label}</option>;
        })}
      </select>
    </div>
  );
}
