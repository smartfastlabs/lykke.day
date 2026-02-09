import { Component, For, Show, createEffect, onCleanup } from "solid-js";
import { Portal } from "solid-js/web";
import { Icon } from "@/components/shared/Icon";
import {
  faArrowLeft,
  faBan,
  faCheck,
  faClock,
  faTriangleExclamation,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";
import type { CalendarEntryAttendanceStatus } from "@/types/api";

type AttendanceStatusOption = {
  status: CalendarEntryAttendanceStatus | null;
  label: string;
  icon: typeof faCheck;
  tone: "positive" | "neutral" | "negative";
};

export type AttendanceStatusModalDirection = "positive" | "negative";

type AttendanceStatusModalProps = {
  isOpen: boolean;
  direction: AttendanceStatusModalDirection;
  title?: string;
  subtitle?: string;
  meetingHasStarted?: boolean;
  currentStatus?: CalendarEntryAttendanceStatus | null;
  onClose: () => void;
  onSelect: (status: CalendarEntryAttendanceStatus | null) => void;
};

const POSITIVE_OPTIONS: AttendanceStatusOption[] = [
  { status: "ATTENDING", label: "In it", icon: faCheck, tone: "positive" },
  { status: "COMPLETE", label: "Went", icon: faCheck, tone: "positive" },
  { status: "SNOOZED", label: "Later", icon: faClock, tone: "neutral" },
  { status: null, label: "Clear", icon: faXmark, tone: "neutral" },
];

const NEGATIVE_OPTIONS: AttendanceStatusOption[] = [
  { status: "NOT_GOING", label: "Not going", icon: faBan, tone: "negative" },
  {
    status: "DIDNT_HAPPEN",
    label: "Didn’t happen",
    icon: faXmark,
    tone: "negative",
  },
  {
    status: "MISSED",
    label: "Missed",
    icon: faTriangleExclamation,
    tone: "negative",
  },
  { status: null, label: "Clear", icon: faXmark, tone: "neutral" },
];

const toneClasses = (
  tone: AttendanceStatusOption["tone"],
  selected: boolean,
): string => {
  const base =
    "flex h-20 w-20 items-center justify-center rounded-full border text-white shadow-lg transition";

  if (tone === "positive") {
    return `${base} ${
      selected
        ? "border-emerald-200/80 bg-emerald-500"
        : "border-emerald-200/70 bg-emerald-500/85 hover:bg-emerald-400"
    }`;
  }

  if (tone === "negative") {
    return `${base} ${
      selected
        ? "border-rose-200/80 bg-rose-500"
        : "border-rose-200/70 bg-rose-500/85 hover:bg-rose-400"
    }`;
  }

  return `${base} ${
    selected
      ? "border-amber-200/80 bg-amber-500"
      : "border-amber-200/70 bg-amber-500/80 hover:bg-amber-400"
  }`;
};

const AttendanceStatusModal: Component<AttendanceStatusModalProps> = (
  props,
) => {
  createEffect(() => {
    if (!props.isOpen) return;

    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        props.onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    onCleanup(() => window.removeEventListener("keydown", handleKeyDown));
  });

  const options = () => {
    if (props.direction === "positive") return POSITIVE_OPTIONS;

    const hasStarted = props.meetingHasStarted ?? false;
    // Before the meeting starts: allow NOT_GOING, but don't allow MISSED.
    // After the meeting has started: allow MISSED, but don't allow NOT_GOING.
    return NEGATIVE_OPTIONS.filter((option) => {
      if (option.status === "MISSED") return hasStarted;
      if (option.status === "NOT_GOING") return !hasStarted;
      return true;
    });
  };

  const headerTitle = () =>
    props.title ??
    (props.direction === "positive" ? "Mark attendance" : "Not attending");

  return (
    <Show when={props.isOpen}>
      <Portal>
        <div
          class="fixed inset-0 z-[60] flex items-center justify-center"
          onClick={() => props.onClose()}
        >
          <div class="absolute inset-0 bg-stone-900/45 backdrop-blur-[1px]" />
          <div
            class="relative flex h-full w-full flex-col items-center justify-center gap-6 px-6"
            onClick={(event) => event.stopPropagation()}
          >
            <div class="text-center space-y-1">
              <p class="text-xs uppercase tracking-[0.2em] text-stone-200/80">
                {headerTitle()}
              </p>
              <Show when={props.subtitle}>
                <p class="text-xs text-stone-200/70">{props.subtitle}</p>
              </Show>
            </div>

            <div class="grid grid-cols-2 gap-x-10 gap-y-6">
              <For each={options()}>
                {(option) => {
                  const isSelected = () =>
                    option.status === props.currentStatus;
                  return (
                    <button
                      type="button"
                      onClick={() => props.onSelect(option.status)}
                      class="flex flex-col items-center gap-2"
                    >
                      <span class={toneClasses(option.tone, isSelected())}>
                        <Icon icon={option.icon} class="h-7 w-7 fill-current" />
                      </span>
                      <span class="text-xs text-stone-200/85">
                        {option.label}
                      </span>
                    </button>
                  );
                }}
              </For>
            </div>

            <button
              type="button"
              onClick={() => props.onClose()}
              class="mt-2 flex items-center gap-2 text-xs text-stone-200/70 underline-offset-2 transition hover:text-white hover:underline"
            >
              <Icon icon={faArrowLeft} class="h-3 w-3 fill-current" />
              Back
            </button>
          </div>
        </div>
      </Portal>
    </Show>
  );
};

export default AttendanceStatusModal;
