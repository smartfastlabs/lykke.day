import { Component } from "solid-js";

interface MotivationalQuoteProps {
  quote: string;
  author: string;
  delay?: string;
  opacity?: number;
}

export const MotivationalQuote: Component<MotivationalQuoteProps> = (props) => {
  return (
    <div
      class="mt-12 transition-all duration-1000 ease-out"
      style={{
        opacity: props.opacity ?? 1,
        transform: props.opacity === 1 ? "translateY(0)" : "translateY(20px)",
        "transition-delay": props.delay ?? "500ms",
      }}
    >
      <div class="max-w-2xl mx-auto">
        <div class="relative py-8 px-6">
          <div class="absolute left-0 top-0 w-8 h-8 border-l-2 border-t-2 border-amber-300/50" />
          <div class="absolute right-0 bottom-0 w-8 h-8 border-r-2 border-b-2 border-amber-300/50" />
          <p
            class="text-stone-600 text-base md:text-lg italic leading-relaxed text-center"
            style={{
              "font-family": "'Cormorant Garamond', Georgia, serif",
            }}
          >
            "{props.quote}"
          </p>
          <p class="text-stone-400 text-sm text-center mt-4">— {props.author}</p>
        </div>
      </div>
    </div>
  );
};
