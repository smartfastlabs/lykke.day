import { useLocation, useNavigate } from "@solidjs/router";
import {
  Component,
  Show,
  createMemo,
  createSignal,
  onCleanup,
} from "solid-js";
import { Icon } from "@/components/shared/Icon";
import AddActionModal from "@/components/shared/AddActionModal";
import AddEventModal from "@/components/events/AddEventModal";
import ModalOverlay from "@/components/shared/ModalOverlay";
import { useStreamingData } from "@/providers/streamingData";
import {
  faHouse,
  faMicrophone,
  faPlus,
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
  const location = useLocation();
  const { addBrainDump, isLoading, sync } = useStreamingData();
  const [isModalOpen, setIsModalOpen] = createSignal(false);
  const [isAddModalOpen, setIsAddModalOpen] = createSignal(false);
  const [showAddEventModal, setShowAddEventModal] = createSignal(false);
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
      windowTyped.SpeechRecognition ??
      windowTyped.webkitSpeechRecognition ??
      null
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

  const openAddModal = () => {
    setIsAddModalOpen(true);
  };

  const closeAddModal = () => {
    setIsAddModalOpen(false);
  };

  const isOnMeHome = createMemo(() => location.pathname === "/me/today");

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
      await addBrainDump(text);
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
            onClick={() => {
              if (isOnMeHome()) {
                openAddModal();
                return;
              }
              navigate("/me/today");
            }}
            class="flex h-10 w-10 items-center justify-center rounded-full border border-stone-200 bg-white/80 text-stone-600 shadow-lg shadow-stone-900/5 transition hover:bg-white active:scale-95"
            aria-label={isOnMeHome() ? "Add" : "Go to home"}
          >
            <Icon
              icon={isOnMeHome() ? faPlus : faHouse}
              class="h-5 w-5 fill-current"
            />
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

      <AddActionModal
        isOpen={isAddModalOpen()}
        onClose={closeAddModal}
        onAddTask={() => {
          closeAddModal();
          navigate("/me/adhoc-task");
        }}
        onAddReminder={() => {
          closeAddModal();
          navigate("/me/add-reminder");
        }}
        onAddAlarm={() => {
          closeAddModal();
          navigate("/me/add-alarm");
        }}
        onAddEvent={() => {
          closeAddModal();
          setShowAddEventModal(true);
        }}
      />

      <AddEventModal
        isOpen={showAddEventModal()}
        onClose={() => setShowAddEventModal(false)}
        defaultDate={new Date().toISOString().slice(0, 10)}
        onCreated={() => {
          sync();
          setShowAddEventModal(false);
        }}
      />

      <ModalOverlay
        isOpen={isModalOpen()}
        onClose={closeDictationModal}
        contentClass="relative flex flex-col items-center justify-center"
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
      </ModalOverlay>
    </>
  );
};

export default BrainDumpButton;
