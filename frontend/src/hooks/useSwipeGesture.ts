import { createSignal } from "solid-js";

interface SwipeCallbacks {
  onSwipeRight: () => void;
  onSwipeLeft: () => void;
  threshold?: number;
}

export function useSwipeGesture(callbacks: SwipeCallbacks) {
  const [translateX, setTranslateX] = createSignal(0);
  let startX = 0;
  let startY = 0;
  let isSwiping = false;
  const threshold = callbacks.threshold ?? 100;

  const handleTouchStart = (e: TouchEvent) => {
    const touch = e.touches[0];
    startX = touch.clientX;
    startY = touch.clientY;
    isSwiping = false;
  };

  const handleTouchMove = (e: TouchEvent) => {
    const touch = e.touches[0];
    const dx = touch.clientX - startX;
    const dy = touch.clientY - startY;

    // Detect if user is swiping horizontally or vertically
    if (!isSwiping) {
      if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 10) {
        isSwiping = true;
      } else if (Math.abs(dy) > 10) {
        // user is scrolling vertically — bail out
        return;
      }
    }

    if (isSwiping) {
      e.preventDefault(); // only prevent default when actually swiping horizontally
      setTranslateX(dx);
    }
  };

  const handleTouchEnd = () => {
    if (isSwiping) {
      const x = translateX();
      if (x > threshold) {
        callbacks.onSwipeRight();
      } else if (x < -threshold) {
        callbacks.onSwipeLeft();
      }
      setTranslateX(0);
    }
    isSwiping = false;
  };

  return {
    translateX,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
  };
}
