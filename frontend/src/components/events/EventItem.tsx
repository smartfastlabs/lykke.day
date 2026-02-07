import { Component, Show, createMemo, createSignal } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import type { CalendarEntryAttendanceStatus, Event } from "@/types/api";
import { getTypeIcon } from "@/utils/icons";
import { formatByFrequency } from "@/components/recurring-events/recurrenceFormat";
import AttendanceStatusModal, {
  AttendanceStatusModalDirection,
} from "@/components/events/AttendanceStatusModal";
import { useStreamingData } from "@/providers/streamingData";
import {
  faBan,
  faCheckCircle,
  faClock,
  faCircleXmark,
  faPersonCircleCheck,
  faTriangleExclamation,
} from "@fortawesome/free-solid-svg-icons";

export interface EventItemProps {
  event: Event;
}

const formatDateTime = (dateTimeStr: string): string => {
  const date = new Date(dateTimeStr);
  return date
    .toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    .toLowerCase()
    .replace(" ", "");
};

const formatCategory = (category?: Event["category"]): string =>
  (category ?? "OTHER").toLowerCase().replace("_", " ");

export const EventItem: Component<EventItemProps> = (props) => {
  const { updateEventAttendanceStatus, now } = useStreamingData();
  const icon = () => getTypeIcon("EVENT");
  const categoryLabel = () => formatCategory(props.event.category);
  const frequencyLabel = () => formatByFrequency(props.event.frequency);
  const meetingHasStarted = createMemo(() => {
    const startsAtMs = new Date(props.event.starts_at).getTime();
    return Number.isFinite(startsAtMs) ? startsAtMs <= now().getTime() : false;
  });

  const attendanceStatus = createMemo(
    () => props.event.attendance_status ?? null,
  );

  const shouldShowStatusIcon = createMemo(() => Boolean(attendanceStatus()));

  const statusIcon = createMemo(() => {
    const status = attendanceStatus();
    if (!status) return null;

    switch (status) {
      case "COMPLETE":
        return { icon: faCheckCircle, class: "fill-emerald-600" };
      case "ATTENDING":
        return { icon: faPersonCircleCheck, class: "fill-emerald-600" };
      case "SNOOZED":
        return { icon: faClock, class: "fill-amber-600" };
      case "NOT_GOING":
        return { icon: faBan, class: "fill-rose-600" };
      case "DIDNT_HAPPEN":
        return { icon: faCircleXmark, class: "fill-rose-600" };
      case "MISSED":
        return { icon: faTriangleExclamation, class: "fill-rose-600" };
      default:
        return null;
    }
  });

  const [dragX, setDragX] = createSignal(0);
  const [isDragging, setIsDragging] = createSignal(false);
  const [modalDirection, setModalDirection] =
    createSignal<AttendanceStatusModalDirection>("positive");
  const [isModalOpen, setIsModalOpen] = createSignal(false);
  const backgroundOpacity = createMemo(() => {
    if (!isDragging()) return 0;
    const abs = Math.abs(dragX());
    if (abs < 6) return 0;
    return clamp(abs / 40, 0, 1);
  });

  const leftOpacity = createMemo(() => (dragX() < 0 ? backgroundOpacity() : 0));
  const rightOpacity = createMemo(() =>
    dragX() > 0 ? backgroundOpacity() : 0,
  );

  let startX = 0;
  let activePointerId: number | null = null;
  const THRESHOLD_PX = 70;
  const MAX_DRAG_PX = 110;

  const clamp = (value: number, min: number, max: number) =>
    Math.min(max, Math.max(min, value));

  const openModal = (direction: AttendanceStatusModalDirection) => {
    setModalDirection(direction);
    setIsModalOpen(true);
  };

  const handlePointerDown = (event: globalThis.PointerEvent) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    startX = event.clientX;
    activePointerId = event.pointerId;
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
    setIsDragging(true);
  };

  const handlePointerMove = (event: globalThis.PointerEvent) => {
    if (!isDragging()) return;
    if (activePointerId !== event.pointerId) return;
    const delta = event.clientX - startX;
    setDragX(clamp(delta, -MAX_DRAG_PX, MAX_DRAG_PX));
  };

  const finishDrag = () => {
    const delta = dragX();
    setIsDragging(false);
    setDragX(0);
    activePointerId = null;

    if (delta > THRESHOLD_PX) {
      openModal("positive");
    } else if (delta < -THRESHOLD_PX) {
      openModal("negative");
    }
  };

  const handlePointerUp = (event: globalThis.PointerEvent) => {
    if (activePointerId !== event.pointerId) return;
    finishDrag();
  };

  const handlePointerCancel = (event: globalThis.PointerEvent) => {
    if (activePointerId !== event.pointerId) return;
    finishDrag();
  };

  const handleSelectStatus = async (
    status: CalendarEntryAttendanceStatus | null,
  ) => {
    setIsModalOpen(false);
    await updateEventAttendanceStatus(props.event, status);
  };

  return (
    <>
      <div class="relative overflow-hidden rounded-2xl border border-white/70 bg-white/70 shadow-lg shadow-amber-900/5 backdrop-blur-sm">
        {/* Swipe hint backgrounds */}
        <div class="pointer-events-none absolute inset-0">
          <div
            class="absolute inset-y-0 left-0 w-1/2 bg-rose-500/15 transition-opacity duration-150"
            style={{ opacity: leftOpacity() }}
          />
          <div
            class="absolute inset-y-0 right-0 w-1/2 bg-emerald-500/15 transition-opacity duration-150"
            style={{ opacity: rightOpacity() }}
          />
          <div class="absolute inset-0 flex items-center justify-between px-4">
            <div
              class="flex items-center gap-2 text-rose-700/70 text-xs transition-opacity duration-150"
              style={{ opacity: leftOpacity() }}
            >
              <Show
                when={meetingHasStarted()}
                fallback={
                  <>
                    <Icon icon={faBan} class="w-4 h-4 fill-rose-600/70" />
                    <span>Not going</span>
                  </>
                }
              >
                <Icon
                  icon={faTriangleExclamation}
                  class="w-4 h-4 fill-rose-600/70"
                />
                <span>Missed</span>
              </Show>
            </div>
            <div
              class="flex items-center gap-2 text-emerald-700/70 text-xs transition-opacity duration-150"
              style={{ opacity: rightOpacity() }}
            >
              <Icon icon={faCheckCircle} class="w-4 h-4 fill-emerald-600/70" />
              <span>Positive</span>
            </div>
          </div>
        </div>

        {/* Foreground content */}
        <div
          class="relative px-4 py-3"
          style={{
            transform: `translateX(${dragX()}px)`,
            transition: isDragging() ? "none" : "transform 150ms ease-out",
            "touch-action": "pan-y",
          }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerCancel}
        >
          <div class="flex items-start gap-3">
            <div class="mt-0.5">
              <Show when={icon()}>
                <Icon icon={icon()!} class="w-4 h-4" />
              </Show>
            </div>
            <div class="flex-1">
              <div class="flex items-start justify-between gap-2">
                <p class="text-sm font-semibold text-stone-800">
                  {props.event.name}
                </p>
                <Show when={shouldShowStatusIcon() && statusIcon()}>
                  {(value) => (
                    <button
                      type="button"
                      class="mt-0.5 inline-flex items-center justify-center rounded-full p-1.5 hover:bg-stone-100/70 transition"
                      aria-label="Change attendance status"
                      title="Change attendance status"
                      onClick={() => openModal("positive")}
                    >
                      <Icon
                        icon={value().icon}
                        class={`w-4 h-4 ${value().class}`}
                      />
                    </button>
                  )}
                </Show>
              </div>
              <div class="flex items-center gap-2 mt-1 flex-wrap">
                <p class="text-xs text-stone-500">
                  {formatDateTime(props.event.starts_at)}
                </p>
                <span class="text-[10px] font-medium uppercase tracking-wide text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">
                  {categoryLabel()}
                </span>
                <span class="text-[10px] font-medium uppercase tracking-wide text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">
                  {frequencyLabel()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <AttendanceStatusModal
        isOpen={isModalOpen()}
        direction={modalDirection()}
        subtitle={props.event.name}
        meetingHasStarted={meetingHasStarted()}
        currentStatus={attendanceStatus()}
        onClose={() => setIsModalOpen(false)}
        onSelect={(status) => {
          void handleSelectStatus(status);
        }}
      />
    </>
  );
};
