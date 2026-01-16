import { Component, JSX, createSignal, onMount } from "solid-js";
import { isBackForwardNavigation } from "@/utils/navigation";

interface AnimatedSectionProps {
  delay?: string;
  children: JSX.Element;
}

export const AnimatedSection: Component<AnimatedSectionProps> = (props) => {
  const [mounted, setMounted] = createSignal(false);

  onMount(() => {
    // Skip animations if navigating via back/forward buttons
    if (isBackForwardNavigation()) {
      setMounted(true);
    } else {
      setTimeout(() => setMounted(true), 50);
    }
  });

  return (
    <div
      class="transition-all duration-1000 ease-out"
      style={{
        opacity: mounted() ? 1 : 0,
        transform: mounted() ? "translateY(0)" : "translateY(20px)",
        "transition-delay": props.delay ?? "200ms",
      }}
    >
      {props.children}
    </div>
  );
};
