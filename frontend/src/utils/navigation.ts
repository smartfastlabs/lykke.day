import { Accessor, createSignal, onMount } from "solid-js";

/**
 * Hook to manage page animations that should only play once per session.
 * Uses sessionStorage to track whether animations have been shown.
 * 
 * @param key - Unique identifier for this page/component's animations
 * @param delay - Delay in milliseconds before showing animations (default: 50)
 * @returns A signal that becomes true when animations should be shown
 * 
 * @example
 * ```tsx
 * const mounted = usePageAnimation("resources-page");
 * 
 * return (
 *   <div style={{ opacity: mounted() ? 1 : 0 }}>
 *     Content
 *   </div>
 * );
 * ```
 */
export function usePageAnimation(
  key: string,
  delay: number = 50
): Accessor<boolean> {
  const [mounted, setMounted] = createSignal(false);
  const storageKey = `page-animation-${key}`;

  onMount(() => {
    // Check if we've already shown animations in this session
    const hasAnimated = sessionStorage.getItem(storageKey) === "true";

    if (hasAnimated) {
      // Skip animations if we've already shown them
      setMounted(true);
    } else {
      // Mark as animated and play animations after delay
      sessionStorage.setItem(storageKey, "true");
      setTimeout(() => setMounted(true), delay);
    }
  });

  return mounted;
}
