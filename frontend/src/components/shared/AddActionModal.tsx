import { Component } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import ModalOverlay from "@/components/shared/ModalOverlay";
import {
  faBell,
  faBullseye,
  faCalendarPlus,
  faListCheck,
  faPlus,
} from "@fortawesome/free-solid-svg-icons";

type AddActionModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onAddTask: () => void;
  onAddReminder: () => void;
  onAddAlarm: () => void;
  onAddEvent?: () => void;
};

const AddActionModal: Component<AddActionModalProps> = (props) => {
  return (
    <ModalOverlay
      isOpen={props.isOpen}
      onClose={props.onClose}
      overlayClass="fixed inset-0 z-[60] flex items-center justify-center px-6"
      contentClass="relative w-full max-w-sm sm:max-w-md"
    >
      <div class="flex flex-col items-center justify-center gap-6">
        <div class="text-center space-y-1">
          <p class="text-xs uppercase tracking-[0.2em] text-stone-200/80">
            Add
          </p>
          <p class="text-xs text-stone-200/70">
            Create a task, reminder, alarm, or event
          </p>
        </div>

        <div
          classList={{
            "grid gap-6 text-center text-xs text-stone-200/80": true,
            "grid-cols-3": !props.onAddEvent,
            "grid-cols-2 sm:grid-cols-4": !!props.onAddEvent,
          }}
        >
          <div class="flex flex-col items-center gap-2">
            <button
              type="button"
              onClick={() => props.onAddTask()}
              class="flex h-20 w-20 items-center justify-center rounded-full border border-amber-200/70 bg-amber-500/80 text-white shadow-lg shadow-amber-900/20 transition hover:bg-amber-400"
              aria-label="Add task"
            >
              <Icon icon={faListCheck} class="h-7 w-7 fill-current" />
            </button>
            <span>Task</span>
          </div>
          <div class="flex flex-col items-center gap-2">
            <button
              type="button"
              onClick={() => props.onAddReminder()}
              class="flex h-20 w-20 items-center justify-center rounded-full border border-sky-200/70 bg-sky-500/80 text-white shadow-lg shadow-sky-900/20 transition hover:bg-sky-400"
              aria-label="Add reminder"
            >
              <Icon icon={faBullseye} class="h-7 w-7 fill-current" />
            </button>
            <span>Reminder</span>
          </div>
          <div class="flex flex-col items-center gap-2">
            <button
              type="button"
              onClick={() => props.onAddAlarm()}
              class="flex h-20 w-20 items-center justify-center rounded-full border border-rose-200/70 bg-rose-500/80 text-white shadow-lg shadow-rose-900/20 transition hover:bg-rose-400"
              aria-label="Add alarm"
            >
              <Icon icon={faBell} class="h-7 w-7 fill-current" />
            </button>
            <span>Alarm</span>
          </div>
          {props.onAddEvent && (
            <div class="flex flex-col items-center gap-2">
              <button
                type="button"
                onClick={() => props.onAddEvent!()}
                class="flex h-20 w-20 items-center justify-center rounded-full border border-emerald-200/70 bg-emerald-500/80 text-white shadow-lg shadow-emerald-900/20 transition hover:bg-emerald-400"
                aria-label="Add event"
              >
                <Icon icon={faCalendarPlus} class="h-7 w-7 fill-current" />
              </button>
              <span>Event</span>
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={() => props.onClose()}
          class="flex items-center gap-2 text-xs text-stone-200/70 underline-offset-2 transition hover:text-white hover:underline"
        >
          <Icon icon={faPlus} class="h-3 w-3 fill-current rotate-45" />
          Close
        </button>
      </div>
    </ModalOverlay>
  );
};

export default AddActionModal;
