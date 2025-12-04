import { Component, Show, createMemo, createSignal } from "solid-js";
import type { Task } from "../../types/routines";
import { getTime } from "../../utils/dates";
import TimeBadge from "../shared/timeBadge";
import TaskStatusBadge from "./statusBadge";
import TaskRow from "./row";

interface TaskCardProps {
  task: Task;
  onSwipeRight?: (task: Task) => void;
  onSwipeLeft?: (task: Task) => void;
}

export const TaskCard: Component<TaskCardProps> = (props) => {
  const [translateX, setTranslateX] = createSignal(0);
  let startX = 0;
  let startY = 0;
  let isSwiping = false;

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

      const threshold = 250;
      if (dx > threshold) {
        props.onSwipeRight?.(props.task);
        setTranslateX(0);
        isSwiping = false;
      } else if (dx < -threshold) {
        props.onSwipeLeft?.(props.task);
        setTranslateX(0);
        isSwiping = false;
      }
    }
  };

  const handleTouchEnd = () => {
    if (isSwiping) {
      const x = translateX();
      const threshold = 100;
      if (x > threshold) props.onSwipeRight?.(props.task);
      else if (x < -threshold) props.onSwipeLeft?.(props.task);
      setTranslateX(0);
    }
    isSwiping = false;
  };

  const taskStatus = createMemo(() => {
    return props.task.status;
  });

  return (
    <div
      class="relative w-full overflow-hidden select-none"
      style="touch-action: pan-y"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Background Actions */}
      <div class="absolute inset-0 bg-gray-100 flex justify-between items-center px-6 text-sm font-medium pointer-events-none">
        <span class="text-green-600">✅ Complete Task</span>
        <span class="text-red-600">🗑 Punt Task</span>
      </div>

      {/* Foreground Card */}
      <div
        class="relative bg-gray-100 p-3 transition-transform duration-150 active:scale-[0.97]"
        style={{
          transform: `translateX(${translateX()}px)`,
          transition: translateX() === 0 ? "transform 0.2s ease-out" : "none",
        }}
        role="button"
      >
        <TaskRow {...props.task} />
      </div>
    </div>
  );
};

export default TaskCard;
