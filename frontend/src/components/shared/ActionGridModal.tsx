import { Component, For, Show } from "solid-js";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import { Icon } from "@/components/shared/Icon";
import ModalOverlay from "@/components/shared/ModalOverlay";

export type ActionGridModalAction = {
  label: string;
  icon: IconDefinition;
  onClick: () => void | Promise<void>;
};

type ActionGridModalProps = {
  isOpen: boolean;
  title: string;
  subtitle?: string;
  actions: ActionGridModalAction[];
  onClose: () => void;
};

const ActionGridModal: Component<ActionGridModalProps> = (props) => {
  return (
    <ModalOverlay
      isOpen={props.isOpen}
      onClose={props.onClose}
      overlayClass="fixed inset-0 z-[60] flex items-center justify-center px-6"
      backdropClass="absolute inset-0 bg-stone-950/60 backdrop-blur-[2px]"
      contentClass="relative w-full max-w-sm sm:max-w-md"
    >
      <div class="flex flex-col items-center justify-center gap-6">
        <div class="text-center space-y-1">
          <p class="text-xs uppercase tracking-[0.2em] text-stone-200/80">
            {props.title}
          </p>
          <Show when={props.subtitle}>
            <p class="text-xs text-stone-200/70">{props.subtitle}</p>
          </Show>
        </div>

        <div class="grid grid-cols-3 gap-6">
          <For each={props.actions}>
            {(action) => (
              <button
                type="button"
                onClick={action.onClick}
                class="group flex flex-col items-center gap-2"
                aria-label={action.label}
                title={action.label}
              >
                <span class="flex h-16 w-16 items-center justify-center rounded-full border border-white/60 bg-white/20 text-white shadow-lg shadow-stone-950/30 transition group-hover:bg-white/30">
                  <Icon icon={action.icon} class="h-6 w-6 fill-current" />
                </span>
                <span class="text-xs text-stone-100/90">{action.label}</span>
              </button>
            )}
          </For>
        </div>

        <button
          type="button"
          onClick={() => props.onClose()}
          class="text-xs text-stone-200/70 underline-offset-2 transition hover:text-white hover:underline"
        >
          Close
        </button>
      </div>
    </ModalOverlay>
  );
};

export default ActionGridModal;

