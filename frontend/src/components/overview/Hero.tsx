import { Component, Show } from "solid-js";

export interface HeroProps {
  weekday: string;
  monthDay: string;
  isWorkday: boolean;
  userName?: string;
  greeting?: string;
  description?: string;
}

export const Hero: Component<HeroProps> = (props) => (
  <div class="relative grid md:grid-cols-3 gap-6 items-start">
    <div class="md:col-span-2 space-y-3 pr-28 md:pr-0">
      <p class="text-sm uppercase tracking-[0.2em] text-amber-600/80">
        {props.weekday} {props.monthDay}
      </p>
      <p
        class="text-2xl md:text-3xl text-stone-700 italic"
        style={{ "font-family": "'Cormorant Garamond', Georgia, serif" }}
      >
        {props.greeting ||
          `Good morning${props.userName ? `, ${props.userName}` : ""}.`}
      </p>
      <Show when={props.description}>
        <p class="text-stone-600 max-w-xl leading-relaxed">
          {props.description}
        </p>
      </Show>
    </div>
    <div class="absolute top-0 right-0 flex flex-col items-end gap-2 mt-2">
      <Show when={props.isWorkday}>
        <span class="px-3 py-1.25 md:px-4 md:py-1.5 rounded-full bg-amber-50/95 text-amber-600 text-[11px] md:text-xs font-semibold uppercase tracking-wide border border-amber-100/80 shadow-sm shadow-amber-900/5">
          Workday
        </span>
      </Show>
    </div>
  </div>
);
