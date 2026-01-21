import { Component, JSX, untrack } from "solid-js";
import { useSwipeGesture } from "@/hooks/useSwipeGesture";

interface SwipeableItemProps {
  onSwipeRight: () => void;
  onSwipeLeft: () => void;
  rightLabel: string | JSX.Element;
  leftLabel: string | JSX.Element;
  statusClass?: string;
  threshold?: number;
  children: JSX.Element;
  compact?: boolean;
}

export const SwipeableItem: Component<SwipeableItemProps> = (props) => {
  // Access props with untrack since the hook stores callbacks at initialization
  // If props change, the hook won't see changes anyway, so untrack is appropriate
  const {
    translateX,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
  } = useSwipeGesture(
    untrack(() => ({
      onSwipeRight: props.onSwipeRight,
      onSwipeLeft: props.onSwipeLeft,
      threshold: props.threshold,
    }))
  );

  // Attach global mouse listeners when dragging starts
  const handleMouseDownWithListeners = (e: globalThis.MouseEvent) => {
    handleMouseDown(e);
    // Attach global listeners for mouse move and up
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUpGlobal);
  };

  const handleMouseUpGlobal = () => {
    handleMouseUp();
    // Remove global listeners
    window.removeEventListener("mousemove", handleMouseMove);
    window.removeEventListener("mouseup", handleMouseUpGlobal);
  };

  return (
    <div
      class="relative w-full overflow-hidden select-none"
      style="touch-action: pan-y"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleMouseDownWithListeners}
    >
      <div class="absolute inset-0 bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 flex justify-between items-center px-6 text-sm font-medium pointer-events-none rounded-xl">
        <span class="text-amber-600">{props.rightLabel}</span>
        <span class="text-rose-500">{props.leftLabel}</span>
      </div>

      {/* Foreground Card */}
      <div
        class="relative transition-transform duration-150 active:scale-[0.97]"
        style={{
          transform: `translateX(${translateX()}px)`,
          transition: translateX() === 0 ? "transform 0.2s ease-out" : "none",
        }}
        role="button"
      >
        <div
          class={`group px-5 ${props.compact ? "py-1" : "py-3.5"} bg-white/60 backdrop-blur-sm rounded-xl hover:bg-white/80 hover:shadow-lg hover:shadow-amber-900/5 transition-all duration-300 cursor-pointer ${props.statusClass ?? ""}`}
        >
          {props.children}
        </div>
      </div>
    </div>
  );
};
