import { Component, Show } from "solid-js";

interface QuoteProps {
  quote: string;
  author?: string;
  containerClass?: string;
  quoteClass?: string;
  authorClass?: string;
}

export const Quote: Component<QuoteProps> = (props) => {
  const containerClass = () => props.containerClass ?? "max-w-xl mx-auto";
  const quoteClass = () =>
    props.quoteClass ??
    "text-stone-600 text-lg md:text-xl italic leading-relaxed px-6";
  const authorClass = () =>
    props.authorClass ?? "text-stone-400 text-sm text-center mt-4";

  return (
    <div class={containerClass()}>
      <div class="relative py-8">
        <div class="absolute left-0 top-0 w-8 h-8 border-l-2 border-t-2 border-amber-300/50" />
        <div class="absolute right-0 bottom-0 w-8 h-8 border-r-2 border-b-2 border-amber-300/50" />
        <p
          class={quoteClass()}
          style={{
            "font-family": "'Cormorant Garamond', Georgia, serif",
          }}
        >
          "{props.quote}"
        </p>
        <Show when={props.author}>
          <p class={authorClass()}>— {props.author}</p>
        </Show>
      </div>
    </div>
  );
};
