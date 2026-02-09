import { createSignal } from "solid-js";

interface SwipeCallbacks {
  onSwipeRight: () => void;
  onSwipeLeft: () => void;
  threshold?: number;
}

export function useSwipeGesture(callbacks: SwipeCallbacks) {
  const [translateX, setTranslateX] = createSignal(0);
  const threshold = callbacks.threshold ?? 100;

  let startX = 0;
  let startY = 0;
  let isSwiping = false;

  // Prefer Pointer Events for consistent cross-device behavior.
  // We still keep the swipe math isolated so it's reusable across event types.
  let activePointerId: number | null = null;
  let pointerTarget: HTMLElement | null = null;
  let hasPointerCapture = false;

  const startSwipe = (clientX: number, clientY: number) => {
    startX = clientX;
    startY = clientY;
    isSwiping = false;
    hasPointerCapture = false;
  };

  const updateSwipe = (clientX: number, clientY: number) => {
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

  const finishPointerGesture = () => {
    endSwipe();
    activePointerId = null;
    pointerTarget = null;
    hasPointerCapture = false;
  };

  const handlePointerDown = (event: globalThis.PointerEvent) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    if (event.pointerType === "mouse") {
      // Prevent text selection / drag ghost image while swiping with mouse.
      event.preventDefault();
    }
    activePointerId = event.pointerId;
    pointerTarget = event.currentTarget as HTMLElement;
    startSwipe(event.clientX, event.clientY);
  };

  const handlePointerMove = (event: globalThis.PointerEvent) => {
    if (activePointerId === null) return;
    if (event.pointerId !== activePointerId) return;

    // Once we detect a horizontal swipe, capture the pointer so we keep receiving moves
    // even if the user drags outside the element.
    const prevIsSwiping = isSwiping;
    updateSwipe(event.clientX, event.clientY);
    if (!prevIsSwiping && isSwiping && pointerTarget && !hasPointerCapture) {
      try {
        pointerTarget.setPointerCapture(activePointerId);
        hasPointerCapture = true;
      } catch {
        // Non-fatal: some browsers / edge cases may throw.
      }
    }
  };

  const handlePointerUp = (event: globalThis.PointerEvent) => {
    if (activePointerId === null) return;
    if (event.pointerId !== activePointerId) return;
    finishPointerGesture();
  };

  const handlePointerCancel = (event: globalThis.PointerEvent) => {
    if (activePointerId === null) return;
    if (event.pointerId !== activePointerId) return;
    finishPointerGesture();
  };

  return {
    translateX,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    handlePointerCancel,
  };
}
