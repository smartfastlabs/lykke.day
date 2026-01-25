import { Show, createSignal, type ParentProps } from "solid-js";

const [activeCount, setActiveCount] = createSignal(0);

const decrement = () =>
  setActiveCount((count) => (count > 0 ? count - 1 : 0));

export const globalLoading = {
  start: (): (() => void) => {
    setActiveCount((count) => count + 1);
    return decrement;
  },
  stop: (): void => {
    decrement();
  },
  clear: (): void => {
    setActiveCount(0);
  },
  isLoading: (): boolean => activeCount() > 0,
};

export function LoadingProvider(props: ParentProps) {
  return <>{props.children}</>;
}

export function LoadingIndicator() {
  return (
    <Show when={activeCount() > 0}>
      <div class="fixed inset-0 z-50 pointer-events-none">
        <div class="absolute top-4 left-1/2 -translate-x-1/2 rounded-full border border-white/80 bg-white/80 px-4 py-2 shadow-lg shadow-amber-900/10 backdrop-blur-md">
          <div class="flex items-center gap-2 text-sm font-medium text-stone-700">
            <span
              class="h-4 w-4 animate-spin rounded-full border-2 border-stone-400 border-t-transparent"
              role="status"
              aria-live="polite"
              aria-label="Loading"
            />
            Thinking...
          </div>
        </div>
      </div>
    </Show>
  );
}
