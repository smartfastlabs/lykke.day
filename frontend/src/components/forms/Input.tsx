import { Component, type Accessor, type Setter } from "solid-js";

// Shared input styles
const inputClass = "w-full px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow";

interface InputProps {
  id: string;
  type?: "text" | "email" | "password" | "number" | "time";
  placeholder: string;
  value: Accessor<string>;
  onChange: Setter<string>;
  required?: boolean;
  autocomplete?: string;
  min?: string;
  max?: string;
}

export const Input: Component<InputProps> = (props) => (
  <div>
    <label for={props.id} class="sr-only">
      {props.placeholder}
    </label>
    <input
      id={props.id}
      type={props.type ?? "text"}
      placeholder={props.placeholder}
      value={props.value()}
      onInput={(e) => props.onChange(e.currentTarget.value)}
      class={inputClass}
      required={props.required}
      autocomplete={props.autocomplete}
      min={props.min}
      max={props.max}
    />
  </div>
);

interface TextAreaProps {
  id: string;
  placeholder: string;
  value: Accessor<string>;
  onChange: Setter<string>;
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

interface SelectProps<T extends string> {
  id: string;
  value: Accessor<T>;
  onChange: (value: T) => void;
  options: T[];
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
        {props.placeholder && (
          <option value="">{props.placeholder}</option>
        )}
        {props.options.map((option) => (
          <option value={option}>{option}</option>
        ))}
      </select>
    </div>
  );
}

