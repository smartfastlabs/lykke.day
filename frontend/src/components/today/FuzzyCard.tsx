import { Component, JSX } from "solid-js";

interface FuzzyCardProps {
  class?: string;
  children: JSX.Element;
}

export const FuzzyCard: Component<FuzzyCardProps> = (props) => {
  return (
    <div
      class="relative overflow-hidden rounded-2xl border border-white/70 bg-white/60 shadow-lg shadow-amber-900/5 backdrop-blur-sm pointer-events-none"
      aria-hidden="true"
    >
      <div class="absolute inset-0 bg-gradient-to-br from-white/60 via-white/40 to-amber-50/50 backdrop-blur-md" />
      <div class={`relative opacity-70 ${props.class ?? ""}`}>
        <div class="animate-pulse">{props.children}</div>
      </div>
    </div>
  );
};

interface FuzzyLineProps {
  class?: string;
}

export const FuzzyLine: Component<FuzzyLineProps> = (props) => {
  return (
    <div class={`h-2.5 rounded-full bg-amber-100/90 ${props.class ?? ""}`} />
  );
};
