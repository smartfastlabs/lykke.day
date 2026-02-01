import { Component, type Accessor } from "solid-js";

const inputClass =
  "px-4 py-3 bg-white border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent transition-shadow";

function digitsOnly(value: string): string {
  return value.replace(/\D/g, "");
}

export type CountryCode = "US" | "CA" | "GB" | "AU" | "DE" | "FR";

export interface CountryConfig {
  code: CountryCode;
  dialCode: string;
  label: string;
  digitsMin: number;
  digitsMax: number;
  placeholder: string;
  format: (digits: string) => string;
  widthCh: number;
}

const US_FORMAT = /^(\d{0,3})(\d{0,3})(\d{0,4})$/;
function formatUS(digits: string): string {
  const match = digits.match(US_FORMAT);
  if (!match) return "";
  const [, a, b, c] = match;
  const parts: string[] = [];
  if (a) {
    parts.push(`(${a}`);
    if (a.length === 3) parts.push(") ");
  }
  if (b) {
    parts.push(b);
    if (b.length === 3) parts.push("-");
  }
  if (c) parts.push(c);
  return parts.join("");
}

const GB_FORMAT = /^(\d{0,5})(\d{0,6})$/;
function formatGB(digits: string): string {
  const match = digits.match(GB_FORMAT);
  if (!match) return "";
  const [, a, b] = match;
  if (!a) return "";
  if (a.length === 5 && !b) return `${a} `;
  if (!b) return a;
  return `${a} ${b}`;
}

function formatGeneric(digits: string, groupSize: number = 4): string {
  const groups: string[] = [];
  for (let i = 0; i < digits.length; i += groupSize) {
    groups.push(digits.slice(i, i + groupSize));
  }
  return groups.join(" ");
}

export const COUNTRY_CONFIGS: Record<CountryCode, CountryConfig> = {
  US: {
    code: "US",
    dialCode: "1",
    label: "US",
    digitsMin: 10,
    digitsMax: 10,
    placeholder: "(555) 555-5555",
    format: formatUS,
    widthCh: 15,
  },
  CA: {
    code: "CA",
    dialCode: "1",
    label: "CA",
    digitsMin: 10,
    digitsMax: 10,
    placeholder: "(555) 555-5555",
    format: formatUS,
    widthCh: 15,
  },
  GB: {
    code: "GB",
    dialCode: "44",
    label: "GB",
    digitsMin: 10,
    digitsMax: 11,
    placeholder: "7700 900123",
    format: formatGB,
    widthCh: 15,
  },
  AU: {
    code: "AU",
    dialCode: "61",
    label: "AU",
    digitsMin: 9,
    digitsMax: 9,
    placeholder: "412 345 678",
    format: (d) => formatGeneric(d, 3),
    widthCh: 14,
  },
  DE: {
    code: "DE",
    dialCode: "49",
    label: "DE",
    digitsMin: 10,
    digitsMax: 11,
    placeholder: "151 23456789",
    format: (d) => formatGeneric(d, 3),
    widthCh: 15,
  },
  FR: {
    code: "FR",
    dialCode: "33",
    label: "FR",
    digitsMin: 9,
    digitsMax: 9,
    placeholder: "6 12 34 56 78",
    format: (d) => formatGeneric(d, 2),
    widthCh: 16,
  },
};

interface PhoneInputProps {
  id: string;
  country: CountryCode;
  value: Accessor<string>;
  onChange: (value: string) => void;
  required?: boolean;
}

export const PhoneInput: Component<PhoneInputProps> = (props) => {
  const config = () => COUNTRY_CONFIGS[props.country];

  const handleInput = (e: Event & { currentTarget: { value: string } }) => {
    const raw = e.currentTarget.value;
    const digits = digitsOnly(raw).slice(0, config().digitsMax);
    const formatted = config().format(digits);
    props.onChange(formatted);
  };

  return (
    <input
      id={props.id}
      type="tel"
      inputmode="numeric"
      autocomplete="tel"
      placeholder={config().placeholder}
      value={props.value()}
      onInput={handleInput}
      class={inputClass}
      style={{ width: `${config().widthCh}ch` }}
      required={props.required}
      maxlength={config().placeholder.length + 2}
      title={`Enter a valid ${config().label} phone number`}
      aria-label="Phone number"
    />
  );
};
