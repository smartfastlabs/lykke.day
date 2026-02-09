import {
  Component,
  For,
  Show,
  createEffect,
  createSignal,
  onCleanup,
} from "solid-js";
import { Portal } from "solid-js/web";
import { Icon } from "@/components/shared/Icon";
import {
  faArrowLeft,
  faClock,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";

type SnoozeOption = {
  label: string;
  minutes: number;
};

type SnoozeActionModalProps = {
  isOpen: boolean;
  title?: string;
  subtitle?: string;
  onClose: () => void;
  onPunt: () => void;
  onSnooze: (minutes: number) => void;
};

const DEFAULT_OPTIONS: SnoozeOption[] = [
  { label: "10 min", minutes: 10 },
  { label: "1 hour", minutes: 60 },
  { label: "3 hours", minutes: 180 },
  { label: "1 day", minutes: 1440 },
];

const SnoozeActionModal: Component<SnoozeActionModalProps> = (props) => {
  const [step, setStep] = createSignal<"choice" | "duration">("choice");

  createEffect(() => {
    if (!props.isOpen) {
      setStep("choice");
    }
  });

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
                {props.title ?? "Punt or Snooze"}
              </p>
              <Show when={props.subtitle}>
                <p class="text-xs text-stone-200/70">{props.subtitle}</p>
              </Show>
            </div>

          <Show when={step() === "choice"}>
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
                onClick={() => setStep("duration")}
                class="flex h-20 w-20 items-center justify-center rounded-full border border-amber-200/70 bg-amber-500/80 text-white shadow-lg shadow-amber-900/20 transition hover:bg-amber-400"
                aria-label="Snooze"
              >
                <Icon icon={faClock} class="h-7 w-7 fill-current" />
              </button>
            </div>
            <div class="flex items-center justify-center gap-10 text-xs text-stone-200/80">
              <span>Punt</span>
              <span>Snooze</span>
            </div>
            <button
              type="button"
              onClick={() => props.onClose()}
              class="text-xs text-stone-200/70 underline-offset-2 transition hover:text-white hover:underline"
            >
              Cancel
            </button>
          </Show>

          <Show when={step() === "duration"}>
            <div class="flex flex-col items-center gap-3">
              <For each={DEFAULT_OPTIONS}>
                {(option) => (
                  <button
                    type="button"
                    onClick={() => props.onSnooze(option.minutes)}
                    class="min-w-[180px] rounded-full border border-white/40 bg-white/15 px-4 py-2 text-sm font-semibold text-stone-100 transition hover:bg-white/25"
                  >
                    {option.label}
                  </button>
                )}
              </For>
              <button
                type="button"
                onClick={() => setStep("choice")}
                class="mt-2 flex items-center gap-2 text-xs text-stone-200/70 underline-offset-2 transition hover:text-white hover:underline"
              >
                <Icon icon={faArrowLeft} class="h-3 w-3 fill-current" />
                Back
              </button>
            </div>
          </Show>
          </div>
        </div>
      </Portal>
    </Show>
  );
};

export default SnoozeActionModal;
