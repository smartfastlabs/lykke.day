import { Component, Show, createEffect, onCleanup } from "solid-js";
import type { JSX } from "solid-js";
import { Portal } from "solid-js/web";

type ModalOverlayProps = {
  isOpen: boolean;
  onClose: () => void;
  children: JSX.Element;
  closeOnEscape?: boolean;
  closeOnBackdrop?: boolean;
  overlayClass?: string;
  backdropClass?: string;
  contentClass?: string;
};

const DEFAULT_OVERLAY_CLASS =
  "fixed inset-0 z-[60] flex items-center justify-center";
const DEFAULT_BACKDROP_CLASS = "absolute inset-0 bg-stone-900/45 backdrop-blur-[1px]";
const DEFAULT_CONTENT_CLASS = "relative";

const ModalOverlay: Component<ModalOverlayProps> = (props) => {
  createEffect(() => {
    const isOpen = props.isOpen;
    const shouldCloseOnEscape = props.closeOnEscape ?? true;
    if (!isOpen || !shouldCloseOnEscape) return;

    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      props.onClose();
    };

    window.addEventListener("keydown", handleKeyDown);
    onCleanup(() => window.removeEventListener("keydown", handleKeyDown));
  });

  const handleBackdropClick = () => {
    const shouldCloseOnBackdrop = props.closeOnBackdrop ?? true;
    if (!shouldCloseOnBackdrop) return;
    props.onClose();
  };

  return (
    <Show when={props.isOpen}>
      <Portal>
        <div
          class={props.overlayClass ?? DEFAULT_OVERLAY_CLASS}
          onClick={handleBackdropClick}
        >
          <div class={props.backdropClass ?? DEFAULT_BACKDROP_CLASS} />
          <div
            class={props.contentClass ?? DEFAULT_CONTENT_CLASS}
            onClick={(event) => event.stopPropagation()}
          >
            {props.children}
          </div>
        </div>
      </Portal>
    </Show>
  );
};

export default ModalOverlay;

