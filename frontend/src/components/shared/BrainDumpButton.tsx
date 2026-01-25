import { useNavigate } from "@solidjs/router";
import {
  Component,
  Show,
  createEffect,
  createMemo,
  createSignal,
  onCleanup,
} from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streamingData";
import {
  faHouse,
  faMicrophone,
  faStop,
} from "@fortawesome/free-solid-svg-icons";

type SpeechRecognitionResultLike = {
  isFinal: boolean;
  0: { transcript: string };
};

type SpeechRecognitionEventLike = {
  resultIndex?: number;
  results: ArrayLike<SpeechRecognitionResultLike>;
};

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

const BrainDumpButton: Component = () => {
  const navigate = useNavigate();
  const { addBrainDumpItem, isLoading } = useStreamingData();
  const [isModalOpen, setIsModalOpen] = createSignal(false);
  const [newItemText, setNewItemText] = createSignal("");
  const [dictationInterim, setDictationInterim] = createSignal("");
  const [isDictating, setIsDictating] = createSignal(false);
  const [isSaving, setIsSaving] = createSignal(false);
  const [dictationError, setDictationError] = createSignal<string | null>(null);
  const [manualStop, setManualStop] = createSignal(false);
  const [hasTranscript, setHasTranscript] = createSignal(false);

  const speechRecognitionCtor = createMemo(() => {
    const windowTyped = window as unknown as {
      SpeechRecognition?: SpeechRecognitionConstructor;
      webkitSpeechRecognition?: SpeechRecognitionConstructor;
    };
    return (
      windowTyped.SpeechRecognition ?? windowTyped.webkitSpeechRecognition ?? null
    );
  });

  let recognition: SpeechRecognitionLike | null = null;
  const appendTranscript = (transcript: string) => {
    const cleaned = transcript.trim();
    if (!cleaned) return;
    setHasTranscript(true);
    setNewItemText((prev) => {
      const spacer = prev && !prev.endsWith(" ") ? " " : "";
      return `${prev}${spacer}${cleaned}`;
    });
    setDictationInterim("");
  };

  const finalizeInterim = () => {
    const interim = dictationInterim().trim();
    if (!interim) return;
    appendTranscript(interim);
  };

  const stopDictation = (isManual = false, clearInterim = true) => {
    if (isManual) {
      setManualStop(true);
    }
    recognition?.stop();
    setIsDictating(false);
    if (clearInterim) {
      setDictationInterim("");
    }
  };

  const startDictation = () => {
    const ctor = speechRecognitionCtor();
    if (!ctor) {
      setDictationError("Speech recognition is not supported.");
      return;
    }

    setDictationError(null);
    recognition = new ctor();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.onresult = (event) => {
      let interimText = "";
      const startIndex = event.resultIndex ?? 0;
      for (let i = startIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) {
          appendTranscript(result[0].transcript);
          continue;
        }
        interimText = `${interimText} ${result[0].transcript}`.trim();
      }
      if (interimText) {
        setHasTranscript(true);
      }
      setDictationInterim(interimText);
    };
    recognition.onerror = (event) => {
      setDictationError(event.error);
      stopDictation(true);
    };
    recognition.onend = () => {
      setIsDictating(false);
      finalizeInterim();
      if (manualStop()) {
        setManualStop(false);
        return;
      }
    };
    recognition.start();
    setIsDictating(true);
  };

  const toggleDictation = () => {
    if (isDictating()) {
      stopDictation(true);
      return;
    }
    startDictation();
  };

  const openDictationModal = () => {
    setNewItemText("");
    setDictationInterim("");
    setDictationError(null);
    setIsSaving(false);
    setManualStop(false);
    setHasTranscript(false);
    setIsModalOpen(true);
    startDictation();
  };

  const closeDictationModal = () => {
    stopDictation(true);
    setIsModalOpen(false);
    setNewItemText("");
    setDictationInterim("");
    setDictationError(null);
    setHasTranscript(false);
  };

  const handleSave = async () => {
    if (isSaving() || isLoading()) return;
    finalizeInterim();
    const text = newItemText().trim();
    if (!text) {
      return;
    }

    setIsSaving(true);
    try {
      await addBrainDumpItem(text);
      closeDictationModal();
    } catch (error) {
      console.error("Failed to add brain dump item:", error);
      setIsSaving(false);
    }
  };

  onCleanup(() => {
    recognition?.stop();
  });

  createEffect(() => {
    if (!isModalOpen()) return;
    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeDictationModal();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    onCleanup(() => {
      window.removeEventListener("keydown", handleKeyDown);
    });
  });

  const displayText = createMemo(() => {
    const base = newItemText();
    const interim = dictationInterim();
    if (!interim) return base;
    const spacer = base && !base.endsWith(" ") ? " " : "";
    return `${base}${spacer}${interim}`;
  });

  const isSpeechSupported = createMemo(() => Boolean(speechRecognitionCtor()));
  const handleSaveAndStop = async () => {
    stopDictation(true, false);
    await handleSave();
  };

  const handlePrimaryMicClick = async () => {
    if (hasTranscript()) {
      await handleSaveAndStop();
      return;
    }
    toggleDictation();
  };

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
            onClick={openDictationModal}
            class="flex h-10 w-10 items-center justify-center rounded-full border border-stone-200 bg-white/80 text-stone-600 shadow-lg shadow-stone-900/5 transition hover:bg-white active:scale-95"
            aria-label="Start dictation"
          >
            <Icon icon={faMicrophone} class="h-5 w-5 fill-current" />
          </button>
        </div>
      </div>

      <Show when={isModalOpen()}>
        <div
          class="fixed inset-0 z-[60] flex items-center justify-center"
          onClick={closeDictationModal}
        >
          <div class="absolute inset-0 bg-stone-900/45 backdrop-blur-[1px]" />
          <div
            class="relative flex flex-col items-center justify-center"
            onClick={(event) => event.stopPropagation()}
          >
            <Show when={hasTranscript()}>
              <div class="mb-6 max-w-[320px] rounded-3xl bg-amber-100 px-5 py-4 text-sm text-stone-800 shadow-md shadow-stone-900/10">
                <span class="text-left leading-relaxed">{displayText()}</span>
              </div>
            </Show>
            <button
              type="button"
              onClick={() => void handlePrimaryMicClick()}
              class={`flex h-20 w-20 items-center justify-center rounded-full border shadow-lg transition-colors ${
                hasTranscript()
                  ? "border-amber-200 bg-amber-500 text-white hover:bg-amber-400"
                  : "border-stone-200 bg-stone-100 text-stone-700 hover:bg-stone-50"
              }`}
              aria-label={
                hasTranscript()
                  ? "Stop dictation and save brain dump"
                  : isDictating()
                  ? "Stop dictation"
                  : "Start dictation"
              }
              disabled={isSaving() || isLoading() || !isSpeechSupported()}
            >
              <Icon
                icon={hasTranscript() ? faStop : faMicrophone}
                class={`h-7 w-7 fill-current ${isDictating() ? "animate-pulse" : ""}`}
              />
            </button>
            <Show when={dictationError()}>
              <p class="mt-6 text-xs text-rose-100">
                Dictation stopped: {dictationError()}
              </p>
            </Show>
            <Show when={!isSpeechSupported()}>
              <p class="mt-6 text-xs text-stone-200">
                Speech recognition is not supported.
              </p>
            </Show>
            <Show when={!hasTranscript()}>
              <button
                type="button"
                onClick={closeDictationModal}
                class="mt-6 text-xs text-stone-200/80 underline-offset-2 transition hover:text-white hover:underline"
                aria-label="Cancel dictation"
              >
                Cancel
              </button>
            </Show>
          </div>
        </div>
      </Show>
    </>
  );
};

export default BrainDumpButton;
