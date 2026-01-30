import {
  createEffect,
  createSignal,
  onCleanup,
  onMount,
  untrack,
} from "solid-js";

import { clamp, isBenignSpeechSynthesisError } from "../kioskUtils";

type UnlockState = "idle" | "attempting" | "enabled" | "failed";

type KioskNotificationPayload = {
  message?: string;
  category?: string;
  message_hash?: string;
  created_at?: string;
  triggered_by?: string | null;
};

type LastKioskMessage = {
  message: string;
  created_at?: string;
  triggered_by?: string | null;
};

type TopicEvent = { event_data?: unknown };

export type SubscribeToTopic = (
  topic: string,
  handler: (event: TopicEvent) => void,
) => () => void;

type VoiceSetting = {
  voice_uri?: unknown;
  rate?: unknown;
  pitch?: unknown;
  volume?: unknown;
} | null;

export function useSpeechSynthesis(options: {
  subscribeToTopic: SubscribeToTopic;
  loadVoiceSetting: () => VoiceSetting;
}) {
  const [ttsSupported, setTtsSupported] = createSignal(false);
  const [speechUnlocked, setSpeechUnlocked] = createSignal(false);
  const [voices, setVoices] = createSignal<globalThis.SpeechSynthesisVoice[]>(
    [],
  );
  const [unlockState, setUnlockState] = createSignal<UnlockState>("idle");
  const [queuedKioskMessages, setQueuedKioskMessages] = createSignal<string[]>(
    [],
  );
  const [lastKioskMessage, setLastKioskMessage] =
    createSignal<LastKioskMessage | null>(null);
  const [ttsLastError, setTtsLastError] = createSignal<string | null>(null);
  const [processedNotificationHashes, setProcessedNotificationHashes] =
    createSignal<Set<string>>(new Set());

  const loadVoices = () => {
    if (!("speechSynthesis" in window)) return;
    setVoices(window.speechSynthesis.getVoices() ?? []);
  };

  const getBestAvailableVoice = (preferredVoiceURI: string | null) => {
    const available = voices();
    if (available.length === 0) {
      return null;
    }

    const exact =
      preferredVoiceURI && preferredVoiceURI.length > 0
        ? (available.find((v) => v.voiceURI === preferredVoiceURI) ?? null)
        : null;
    if (exact) return exact;

    // Favor "default" and/or English voices if present, otherwise use first.
    return (
      available.find((v) => Boolean(v.default)) ??
      available.find((v) => (v.lang ?? "").toLowerCase().startsWith("en")) ??
      available[0] ??
      null
    );
  };

  const unlockSpeech = () => {
    if (speechUnlocked() || !("speechSynthesis" in window)) {
      return;
    }

    setUnlockState("attempting");

    // Many Chromium builds require a direct user interaction before speech works.
    // IMPORTANT: Some engines won't fire `onstart` for an empty string, so use a
    // non-empty utterance and keep it short.
    try {
      if (voices().length === 0) {
        setUnlockState("failed");
        setTtsLastError(
          "No voices available on this device (SpeechSynthesis has no voices).",
        );
        return;
      }

      const utterance = new window.SpeechSynthesisUtterance("Audio enabled.");
      // Keep it quiet but non-zero to avoid "silent utterance" optimizations.
      utterance.volume = 0.05;
      utterance.rate = 1.0;
      const bestVoice = getBestAvailableVoice(null);
      if (bestVoice) {
        utterance.voice = bestVoice;
      }
      utterance.onstart = () => {
        setSpeechUnlocked(true);
        setUnlockState("enabled");
        // Cancel immediately after starting
        window.speechSynthesis.cancel();
      };
      utterance.onerror = (event) => {
        console.error("Unlock speech synthesis error:", event);
        setUnlockState("failed");
        const errValue = (event as unknown as { error?: unknown }).error;
        if (!isBenignSpeechSynthesisError(errValue)) {
          setTtsLastError(
            typeof errValue === "string"
              ? String(errValue)
              : "Speech synthesis failed to start",
          );
        }
      };
      window.speechSynthesis.speak(utterance);

      // If nothing starts shortly, mark as failed (helps on devices that silently no-op).
      window.setTimeout(() => {
        if (!untrack(() => speechUnlocked())) {
          setUnlockState("failed");
        }
      }, 1500);
    } catch (err) {
      console.error("Failed to unlock speech synthesis:", err);
      setUnlockState("failed");
    }
  };

  const speakSample = () => {
    if (!("speechSynthesis" in window)) return;
    try {
      if (voices().length === 0) {
        setTtsLastError(
          "No voices available on this device (SpeechSynthesis has no voices).",
        );
        return;
      }

      window.speechSynthesis.cancel();
      const utterance = new window.SpeechSynthesisUtterance(
        "This is a kiosk voice test.",
      );
      const bestVoice = getBestAvailableVoice(null);
      if (bestVoice) {
        utterance.voice = bestVoice;
      }
      utterance.volume = 1.0;
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.onerror = (event) => {
        console.error("Sample speech synthesis error:", event);
        const errValue = (event as unknown as { error?: unknown }).error;
        if (!isBenignSpeechSynthesisError(errValue)) {
          setTtsLastError(
            typeof errValue === "string"
              ? String(errValue)
              : "Speech synthesis error",
          );
        }
      };
      setTtsLastError(null);
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.error("Failed to play sample:", err);
    }
  };

  const speakQueuedMessages = () => {
    if (!("speechSynthesis" in window)) return;
    if (!speechUnlocked()) return;
    const queue = queuedKioskMessages();
    if (queue.length === 0) return;

    if (voices().length === 0) {
      setTtsLastError(
        "No voices available on this device (SpeechSynthesis has no voices).",
      );
      return;
    }

    const message = queue[0];
    setQueuedKioskMessages(queue.slice(1));

    window.speechSynthesis.cancel();

    const utterance = new window.SpeechSynthesisUtterance(message);
    const voiceSetting = options.loadVoiceSetting();

    const configuredVoiceURI =
      typeof voiceSetting?.voice_uri === "string"
        ? voiceSetting.voice_uri
        : null;
    const bestVoice = getBestAvailableVoice(configuredVoiceURI);
    if (bestVoice) {
      utterance.voice = bestVoice;
    }

    utterance.rate =
      typeof voiceSetting?.rate === "number"
        ? clamp(voiceSetting.rate, 0.5, 2.0)
        : 1.0;
    utterance.pitch =
      typeof voiceSetting?.pitch === "number"
        ? clamp(voiceSetting.pitch, 0.0, 2.0)
        : 1.0;
    utterance.volume =
      typeof voiceSetting?.volume === "number"
        ? clamp(voiceSetting.volume, 0.0, 1.0)
        : 1.0;

    utterance.onerror = (event) => {
      console.error("Speech synthesis error:", event);
      const errValue = (event as unknown as { error?: unknown }).error;
      if (!isBenignSpeechSynthesisError(errValue)) {
        setTtsLastError(
          typeof errValue === "string"
            ? String(errValue)
            : "Speech synthesis error",
        );
      }
    };
    utterance.onend = () => {
      // Continue draining the queue
      const next = () => speakQueuedMessages();
      if (typeof globalThis.queueMicrotask === "function") {
        globalThis.queueMicrotask(next);
      } else {
        void Promise.resolve().then(next);
      }
    };

    setTtsLastError(null);
    window.speechSynthesis.speak(utterance);
  };

  const enqueueKioskMessage = (message: string) => {
    setQueuedKioskMessages((prev) => [...prev, message]);
    // Attempt immediate playback (will no-op if not unlocked)
    speakQueuedMessages();
  };

  onMount(() => {
    setTtsSupported("speechSynthesis" in window);

    if ("speechSynthesis" in window) {
      loadVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        loadVoices();
      };
    }
  });

  // Subscribe to kiosk notification events and handle TTS
  createEffect(() => {
    // Unlock on any user interaction (click, touch, keypress)
    const unlockSpeechFromEvent = () => {
      // Called by the browser, not Solid. Avoid accidental tracking.
      untrack(() => unlockSpeech());
    };

    const unlockEvents = ["click", "touchstart", "keydown"];
    const cleanupUnlockListeners: (() => void)[] = [];
    unlockEvents.forEach((eventType) => {
      document.addEventListener(eventType, unlockSpeechFromEvent, {
        once: true,
        passive: true,
      });
      // Note: Since we use { once: true }, the listener auto-removes after first call
      // But we track it for completeness
      cleanupUnlockListeners.push(() => {
        document.removeEventListener(eventType, unlockSpeechFromEvent);
      });
    });

    const unsubscribe = options.subscribeToTopic(
      "KioskNotificationEvent",
      (event) => {
        const payload = event.event_data as KioskNotificationPayload;

        if (!payload.message || !payload.message_hash) {
          return;
        }

        setLastKioskMessage({
          message: payload.message,
          created_at: payload.created_at,
          triggered_by: payload.triggered_by,
        });

        const hash = payload.message_hash;
        const processed = untrack(() => processedNotificationHashes());
        if (processed.has(hash)) {
          console.log("Skipping duplicate kiosk notification:", hash);
          return;
        }

        setProcessedNotificationHashes((prev) => {
          const next = new Set(prev);
          next.add(hash);
          if (next.size > 100) {
            const entries = Array.from(next);
            entries.shift();
            return new Set(entries);
          }
          return next;
        });

        if (!("speechSynthesis" in window)) {
          console.warn("SpeechSynthesis not available");
          return;
        }

        if (!untrack(() => speechUnlocked())) {
          console.log(
            "Kiosk notification received, but audio is locked. Waiting for user interaction to enable speech.",
          );
        }

        enqueueKioskMessage(payload.message);
      },
    );

    onCleanup(() => {
      unsubscribe();
      // Cancel any ongoing speech
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      // Clean up unlock event listeners
      cleanupUnlockListeners.forEach((cleanup) => cleanup());
    });
  });

  onCleanup(() => {
    // If this page unmounts, avoid leaving speech running.
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  });

  return {
    ttsSupported,
    speechUnlocked,
    voices,
    unlockState,
    queuedKioskMessages,
    lastKioskMessage,
    ttsLastError,
    unlockSpeech,
    speakSample,
    speakQueuedMessages,
    enqueueKioskMessage,
  };
}
