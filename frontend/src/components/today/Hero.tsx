import { Component, Show } from "solid-js";

export interface HeroProps {
  weekday: string;
  monthDay: string;
  isWorkday: boolean;
  userName?: string;
  greeting?: string;
  description?: string;
}

export const Hero: Component<HeroProps> = (props) => {
  return (
    <div class="relative mb-8 md:mb-12">
      {/* Assistant Message */}
      <div class="flex items-start gap-3 mb-3">
        {/* Avatar */}
        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-stone-700 to-stone-800 flex items-center justify-center shadow-md">
          <span class="text-white text-lg">✨</span>
        </div>

        {/* Message Container */}
        <div class="flex-1 max-w-3xl">
          {/* Name and timestamp */}
          <div class="flex items-center gap-2 mb-1.5">
            <span class="text-sm font-semibold text-stone-700">lykke</span>
            <span class="text-xs text-stone-400">
              {props.weekday}, {props.monthDay}
            </span>
            <Show when={props.isWorkday}>
              <span class="px-2 py-0.5 rounded-full bg-amber-400 text-amber-900 text-xs font-bold">
                Workday
              </span>
            </Show>
          </div>

          {/* Message Bubble */}
          <div class="bg-stone-100 border border-stone-200 text-stone-800 rounded-2xl rounded-tl-sm shadow-sm">
            <div class="p-4">
              <Show when={props.description}>
                <p class="text-stone-700 text-sm md:text-base leading-relaxed">
                  {props.description}
                </p>
              </Show>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
