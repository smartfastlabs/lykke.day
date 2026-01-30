import { useNavigate } from "@solidjs/router";
import {
  Component,
  Show,
  createEffect,
  createSignal,
  onCleanup,
} from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streamingData";
import { faHouse, faPenToSquare } from "@fortawesome/free-solid-svg-icons";

const BrainDumpButton: Component = () => {
  const navigate = useNavigate();
  const { addBrainDump, isLoading } = useStreamingData();
  const [isModalOpen, setIsModalOpen] = createSignal(false);
  const [newItemText, setNewItemText] = createSignal("");
  const [isSaving, setIsSaving] = createSignal(false);
  const openModal = () => {
    setNewItemText("");
    setIsSaving(false);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setNewItemText("");
  };

  const handleSave = async () => {
    if (isSaving() || isLoading()) return;
    const text = newItemText().trim();
    if (!text) {
      return;
    }

    setIsSaving(true);
    try {
      await addBrainDump(text);
      closeModal();
    } catch (error) {
      console.error("Failed to add brain dump item:", error);
      setIsSaving(false);
    }
  };

  onCleanup(() => {});

  createEffect(() => {
    if (!isModalOpen()) return;
    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeModal();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    onCleanup(() => {
      window.removeEventListener("keydown", handleKeyDown);
    });
  });

  return (
    <>
      <div class="fixed bottom-6 left-6 z-50 print:hidden">
        <div class="flex items-center gap-2">
          <button
            onClick={() => navigate("/me")}
            class="flex h-10 w-10 items-center justify-center rounded-full border border-stone-200 bg-white/80 text-stone-600 shadow-lg shadow-stone-900/5 transition hover:bg-white active:scale-95"
            aria-label="Go to home"
          >
            <Icon icon={faHouse} class="h-5 w-5 fill-current" />
          </button>
          <button
            onClick={openModal}
            class="flex h-10 w-10 items-center justify-center rounded-full border border-stone-200 bg-white/80 text-stone-600 shadow-lg shadow-stone-900/5 transition hover:bg-white active:scale-95"
            aria-label="Add brain dump"
          >
            <Icon icon={faPenToSquare} class="h-5 w-5 fill-current" />
          </button>
        </div>
      </div>

      <Show when={isModalOpen()}>
        <div
          class="fixed inset-0 z-[60] flex items-center justify-center"
          onClick={closeModal}
        >
          <div class="absolute inset-0 bg-stone-900/45 backdrop-blur-[1px]" />
          <div
            class="relative w-[min(92vw,520px)] rounded-3xl bg-white p-6 shadow-xl shadow-stone-900/20"
            onClick={(event) => event.stopPropagation()}
          >
            <div class="space-y-3">
              <div>
                <div class="text-xs font-semibold uppercase tracking-wide text-stone-400">
                  Brain dump
                </div>
                <p class="mt-1 text-sm text-stone-600">
                  Add a quick note to today.
                </p>
              </div>

              <textarea
                class="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-800 shadow-sm focus:border-amber-300 focus:outline-none"
                rows={5}
                value={newItemText()}
                onInput={(e) => setNewItemText(e.currentTarget.value)}
                placeholder="Type your note…"
              />

              <div class="flex flex-col gap-2 sm:flex-row sm:justify-end">
                <button
                  type="button"
                  onClick={closeModal}
                  class="rounded-full border border-stone-200 bg-white px-5 py-2.5 text-sm font-semibold text-stone-700 shadow-sm transition hover:border-stone-300 hover:text-stone-900"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={isSaving() || isLoading() || !newItemText().trim()}
                  onClick={() => void handleSave()}
                  class="rounded-full bg-stone-900 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSaving() ? "Saving…" : "Save"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Show>
    </>
  );
};

export default BrainDumpButton;
