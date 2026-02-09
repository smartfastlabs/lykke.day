import { Component, Show, createEffect, onCleanup } from "solid-js";
import { Portal } from "solid-js/web";
import { Icon } from "@/components/shared/Icon";
import { faBell, faXmark } from "@fortawesome/free-solid-svg-icons";

type ReminderActionModalProps = {
  isOpen: boolean;
  title?: string;
  subtitle?: string;
  onClose: () => void;
  onPunt: () => void;
  onRemindTomorrow: () => void;
};

const ReminderActionModal: Component<ReminderActionModalProps> = (props) => {
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
                {props.title ?? "Punt or Remind me Tomorrow"}
              </p>
              <Show when={props.subtitle}>
                <p class="text-xs text-stone-200/70">{props.subtitle}</p>
              </Show>
            </div>

            <div class="flex items-center justify-center gap-6">
              <button
                type="button"
                onClick={() => props.onPunt()}
                class="flex h-20 w-20 items-center justify-center rounded-full border border-rose-200/70 bg-rose-500/80 text-white shadow-lg shadow-rose-900/20 transition hover:bg-rose-400"
                aria-label="Punt it"
              >
                <Icon icon={faXmark} class="h-7 w-7 fill-current" />
              </button>
              <button
                type="button"
                onClick={() => props.onRemindTomorrow()}
                class="flex h-20 w-20 items-center justify-center rounded-full border border-amber-200/70 bg-amber-500/80 text-white shadow-lg shadow-amber-900/20 transition hover:bg-amber-400"
                aria-label="Remind me tomorrow"
              >
                <Icon icon={faBell} class="h-7 w-7 fill-current" />
              </button>
            </div>
            <div class="flex items-center justify-center gap-10 text-xs text-stone-200/80">
              <span>Punt</span>
              <span>Tomorrow</span>
            </div>
            <button
              type="button"
              onClick={() => props.onClose()}
              class="text-xs text-stone-200/70 underline-offset-2 transition hover:text-white hover:underline"
            >
              Cancel
            </button>
          </div>
        </div>
      </Portal>
    </Show>
  );
};

export default ReminderActionModal;
