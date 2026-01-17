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

  const startSwipe = (clientX: number, clientY: number) => {
    startX = clientX;
    startY = clientY;
    isSwiping = false;
  };

  const updateSwipe = (clientX: number, clientY: number, preventDefault?: () => void) => {
    const dx = clientX - startX;
    const dy = clientY - startY;

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
      if (preventDefault) {
        preventDefault(); // only prevent default when actually swiping horizontally
      }
      setTranslateX(dx);
    }
  };

  const endSwipe = () => {
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

  // Touch event handlers
  const handleTouchStart = (e: TouchEvent) => {
    const touch = e.touches[0];
    startSwipe(touch.clientX, touch.clientY);
  };

  const handleTouchMove = (e: TouchEvent) => {
    const touch = e.touches[0];
    updateSwipe(touch.clientX, touch.clientY, () => e.preventDefault());
  };

  const handleTouchEnd = () => {
    endSwipe();
  };

  // Mouse event handlers for desktop
  const handleMouseDown = (e: globalThis.MouseEvent) => {
    e.preventDefault();
    startSwipe(e.clientX, e.clientY);
  };

  const handleMouseMove = (e: globalThis.MouseEvent) => {
    updateSwipe(e.clientX, e.clientY);
  };

  const handleMouseUp = () => {
    endSwipe();
  };

  return {
    translateX,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
  };
}
