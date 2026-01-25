import { useNavigate } from "@solidjs/router";
import { Component, Show, createMemo, createSignal, onCleanup } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { useStreamingData } from "@/providers/streamingData";
import {
  faHouse,
  faMicrophone,
  faStop,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";

type SpeechRecognitionResultLike = {
  isFinal: boolean;
  0: { transcript: string };
};

type SpeechRecognitionEventLike = {
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

  const stopDictation = (isManual = false) => {
    if (isManual) {
      setManualStop(true);
    }
    recognition?.stop();
    setIsDictating(false);
    setDictationInterim("");
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
      for (let i = 0; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) {
          appendTranscript(result[0].transcript);
          continue;
        }
        interimText = `${interimText} ${result[0].transcript}`.trim();
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
      if (isModalOpen() && !isSaving()) {
        void handleSave(true);
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
    setIsModalOpen(true);
    startDictation();
  };

  const closeDictationModal = () => {
    stopDictation(true);
    setIsModalOpen(false);
    setNewItemText("");
    setDictationInterim("");
    setDictationError(null);
  };

  const handleSave = async (isAutoSave = false) => {
    if (isSaving() || isLoading()) return;
    finalizeInterim();
    const text = newItemText().trim();
    if (!text) {
      if (isAutoSave) {
        closeDictationModal();
      }
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

  const displayText = createMemo(() => {
    const base = newItemText();
    const interim = dictationInterim();
    if (!interim) return base;
    const spacer = base && !base.endsWith(" ") ? " " : "";
    return `${base}${spacer}${interim}`;
  });

  const isSpeechSupported = createMemo(() => Boolean(speechRecognitionCtor()));

  return (
    <>
      <div class="fixed bottom-6 right-6 z-50 print:hidden">
        <div class="flex items-center gap-2 text-white">
          <button
            onClick={() => navigate("/me")}
            class="flex h-10 w-10 items-center justify-center rounded-full bg-gray-600 shadow-lg transition-transform duration-150 ease-in-out hover:bg-gray-700 active:scale-95"
            aria-label="Go to home"
          >
            <Icon icon={faHouse} class="h-5 w-5 fill-white" />
          </button>
          <button
            onClick={openDictationModal}
            class="flex h-10 w-10 items-center justify-center rounded-full bg-gray-600 shadow-lg transition-transform duration-150 ease-in-out hover:bg-gray-700 active:scale-95"
            aria-label="Start dictation"
          >
            <Icon icon={faMicrophone} class="h-4 w-4 fill-white" />
          </button>
        </div>
      </div>

      <Show when={isModalOpen()}>
        <div class="fixed inset-0 z-[60] flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div class="w-full max-w-md rounded-2xl bg-white px-5 py-4 shadow-2xl">
            <div class="flex items-center justify-between">
              <p class="text-sm font-semibold text-stone-700">Dictation</p>
              <button
                type="button"
                onClick={closeDictationModal}
                class="h-8 w-8 rounded-full flex items-center justify-center text-stone-500 hover:text-stone-700 hover:bg-stone-100"
                aria-label="Close dictation"
              >
                <Icon icon={faXmark} class="h-4 w-4 fill-current" />
              </button>
            </div>

            <textarea
              value={displayText()}
              onInput={(e) => {
                setNewItemText(e.currentTarget.value);
                setDictationInterim("");
              }}
              placeholder="Speak your thoughts..."
              rows={5}
              class="mt-3 w-full resize-none rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-400"
              disabled={isSaving() || isLoading()}
            />

            <div class="mt-3 flex items-center justify-between">
              <span class="text-xs text-stone-500">
                {isDictating()
                  ? "Listening…"
                  : isSpeechSupported()
                  ? "Paused"
                  : "Speech not supported"}
              </span>
              <div class="flex items-center gap-2">
                <Show when={isSpeechSupported()}>
                  <button
                    type="button"
                    onClick={toggleDictation}
                    class={`h-9 w-9 rounded-full flex items-center justify-center border transition-colors ${
                      isDictating()
                        ? "border-rose-200 bg-rose-50 text-rose-600"
                        : "border-stone-200 bg-white text-stone-600 hover:bg-stone-50"
                    }`}
                    aria-label={isDictating() ? "Stop dictation" : "Start dictation"}
                    disabled={isSaving() || isLoading()}
                  >
                    <Icon
                      icon={isDictating() ? faStop : faMicrophone}
                      class="h-4 w-4 fill-current"
                    />
                  </button>
                </Show>
                <button
                  type="button"
                  onClick={() => void handleSave()}
                  disabled={isSaving() || isLoading() || !displayText().trim()}
                  class="h-9 rounded-full bg-stone-900 px-4 text-xs font-semibold text-white transition-colors hover:bg-stone-800 disabled:opacity-50"
                >
                  {isSaving() ? "Saving…" : "Save"}
                </button>
              </div>
            </div>

            <Show when={dictationError()}>
              <p class="mt-2 text-xs text-rose-600">
                Dictation stopped: {dictationError()}
              </p>
            </Show>
          </div>
        </div>
      </Show>
    </>
  );
};

export default BrainDumpButton;
