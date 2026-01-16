import { Component, JSX } from "solid-js";
import { useSwipeGesture } from "@/hooks/useSwipeGesture";

interface SwipeableItemProps {
  onSwipeRight: () => void;
  onSwipeLeft: () => void;
  rightLabel: string | JSX.Element;
  leftLabel: string | JSX.Element;
  statusClass?: string;
  threshold?: number;
  children: JSX.Element;
}

export const SwipeableItem: Component<SwipeableItemProps> = (props) => {
  const { translateX, handleTouchStart, handleTouchMove, handleTouchEnd } =
    useSwipeGesture({
      onSwipeRight: props.onSwipeRight,
      onSwipeLeft: props.onSwipeLeft,
      threshold: props.threshold,
    });

  return (
    <div
      class="relative w-full overflow-hidden select-none mb-3"
      style="touch-action: pan-y"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
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
          class={`group px-5 py-3.5 bg-white/60 backdrop-blur-sm border border-white/80 rounded-xl hover:bg-white/80 hover:shadow-lg hover:shadow-amber-900/5 transition-all duration-300 cursor-pointer ${props.statusClass ?? ""}`}
        >
          {props.children}
        </div>
      </div>
    </div>
  );
};
