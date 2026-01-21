import { Component, Show, createMemo, createSignal, onCleanup } from "solid-js";
import { useNavigate } from "@solidjs/router";
import ModalPage from "@/components/shared/ModalPage";
import FloatingActionButtons from "@/components/shared/FloatingActionButtons";
import { useStreamingData } from "@/providers/streamingData";
import { Icon } from "@/components/shared/Icon";
import {
  faBrain,
  faMicrophone,
  faStop,
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

const BrainDumpDumpPage: Component = () => {
  const navigate = useNavigate();
  const { addBrainDumpItem, isLoading } = useStreamingData();
  const [newItemText, setNewItemText] = createSignal("");
  const [isAdding, setIsAdding] = createSignal(false);
  const [isDictating, setIsDictating] = createSignal(false);
  const [dictationError, setDictationError] = createSignal<string | null>(
    null
  );

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
  };

  const stopDictation = () => {
    recognition?.stop();
    setIsDictating(false);
  };

  const startDictation = () => {
    const ctor = speechRecognitionCtor();
    if (!ctor) return;

    setDictationError(null);
    recognition = new ctor();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.continuous = true;
    recognition.onresult = (event) => {
      for (let i = 0; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) {
          appendTranscript(result[0].transcript);
        }
      }
    };
    recognition.onerror = (event) => {
      setDictationError(event.error);
      stopDictation();
    };
    recognition.onend = () => {
      setIsDictating(false);
    };
    recognition.start();
    setIsDictating(true);
  };

  const toggleDictation = () => {
    if (isDictating()) {
      stopDictation();
      return;
    }
    startDictation();
  };

  const handleSave = async () => {
    const text = newItemText().trim();
    if (!text || isAdding()) return;

    setIsAdding(true);
    try {
      await addBrainDumpItem(text);
      navigate("/me");
    } catch (error) {
      console.error("Failed to add brain dump item:", error);
    } finally {
      setIsAdding(false);
    }
  };

  onCleanup(() => {
    recognition?.stop();
  });

  const isSpeechSupported = createMemo(() => Boolean(speechRecognitionCtor()));

  return (
    <>
      <ModalPage
        subtitle=""
        title={
          <div class="flex items-center justify-center gap-3">
            <Icon icon={faBrain} class="w-6 h-6 fill-sky-600" />
            <p class="text-2xl font-semibold text-stone-800">Brain dump</p>
          </div>
        }
      >
        <div class="space-y-5">
          <textarea
            value={newItemText()}
            onInput={(e) => setNewItemText(e.currentTarget.value)}
            placeholder="Say what you need to say..."
            disabled={isAdding() || isLoading()}
            rows={6}
            class="w-full px-4 py-3 text-base bg-white/80 border border-stone-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed placeholder:text-stone-400 resize-none"
          />

          <div class="flex items-center gap-3">
            <button
              onClick={handleSave}
              disabled={!newItemText().trim() || isAdding() || isLoading()}
              class="flex-1 h-11 flex items-center justify-center bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-sky-500"
            >
              Save & return
            </button>

            <Show when={isSpeechSupported()}>
              <button
                type="button"
                onClick={toggleDictation}
                class={`h-11 w-11 flex items-center justify-center rounded-lg border transition-colors ${
                  isDictating()
                    ? "bg-rose-50 border-rose-200 text-rose-600"
                    : "bg-white border-stone-200 text-stone-600 hover:bg-stone-50"
                }`}
                aria-label={isDictating() ? "Stop dictation" : "Start dictation"}
              >
                <Icon
                  icon={isDictating() ? faStop : faMicrophone}
                  class="w-4 h-4 fill-current"
                />
              </button>
            </Show>
          </div>

          <Show when={dictationError()}>
            <p class="text-xs text-rose-600">
              Dictation stopped: {dictationError()}
            </p>
          </Show>
        </div>
        <div class="pt-1 text-center">
          <button
            type="button"
            onClick={() => navigate("/me/brain-dump")}
            class="text-sm text-amber-700 font-semibold hover:text-amber-800 transition-colors"
          >
            See Today&apos;s Brain Dump
          </button>
        </div>
      </ModalPage>
      <FloatingActionButtons
        rightButton="settings"
        onSettingsClick={() => navigate("/me/settings")}
      />
    </>
  );
};

export default BrainDumpDumpPage;
