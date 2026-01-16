import { Component, JSX, untrack } from "solid-js";
import { usePageAnimation } from "@/utils/navigation";

interface AnimatedSectionProps {
  delay?: string;
  children: JSX.Element;
  animationKey?: string;
}

// Counter to ensure unique keys for AnimatedSection instances
let animatedSectionCounter = 0;

export const AnimatedSection: Component<AnimatedSectionProps> = (props) => {
  // Generate a unique key if not provided, using a counter to ensure uniqueness
  // Store the generated key once per component instance
  let instanceKey: string | undefined;
  const getUniqueKey = (): string => {
    if (instanceKey === undefined) {
      instanceKey = `animated-section-${++animatedSectionCounter}`;
    }
    return instanceKey;
  };
  // Use untrack since we only need the key once at initialization
  const uniqueKey = untrack(() => props.animationKey ?? getUniqueKey());
  const mounted = usePageAnimation(uniqueKey);

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
