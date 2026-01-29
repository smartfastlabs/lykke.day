import { useNavigate } from "@solidjs/router";
import {
  Component,
  For,
  Show,
  createEffect,
  createMemo,
  createSignal,
  onCleanup,
  onMount,
} from "solid-js";

import SettingsPage from "@/components/shared/SettingsPage";
import { useAuth } from "@/providers/auth";
import { globalNotifications } from "@/providers/notifications";
import { authAPI } from "@/utils/api";

type VoiceSetting = {
  voice_uri?: string | null;
  rate?: number | null;
  pitch?: number | null;
  volume?: number | null;
};

const DEFAULT_SAMPLE =
  "Hi. This is a sample. Your next task is to take a deep breath, and keep going.";

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));

const VoiceSettingsPage: Component = () => {
  const navigate = useNavigate();
  const { user, refetch } = useAuth();

  const [voices, setVoices] = createSignal<SpeechSynthesisVoice[]>([]);
  const [sampleText, setSampleText] = createSignal(DEFAULT_SAMPLE);
  const [selectedVoiceURI, setSelectedVoiceURI] = createSignal<string | null>(
    null,
  );
  const [rate, setRate] = createSignal(1.0);
  const [pitch, setPitch] = createSignal(1.0);
  const [volume, setVolume] = createSignal(1.0);
  const [isSaving, setIsSaving] = createSignal(false);

  const loadVoices = () => {
    if (!("speechSynthesis" in window)) {
      setVoices([]);
      return;
    }
    const next = window.speechSynthesis.getVoices() ?? [];
    setVoices(next);
  };

  onMount(() => {
    loadVoices();
    if ("speechSynthesis" in window) {
      window.speechSynthesis.onvoiceschanged = () => {
        loadVoices();
      };
    }
  });

  onCleanup(() => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.onvoiceschanged = null;
      window.speechSynthesis.cancel();
    }
  });

  createEffect(() => {
    const current = user();
    const raw = (current?.settings as { voice_setting?: unknown } | undefined)
      ?.voice_setting;
    const voice = (raw ?? null) as VoiceSetting | null;
    setSelectedVoiceURI(
      typeof voice?.voice_uri === "string" ? voice.voice_uri : null,
    );
    setRate(
      typeof voice?.rate === "number" ? clamp(voice.rate, 0.5, 2.0) : 1.0,
    );
    setPitch(
      typeof voice?.pitch === "number" ? clamp(voice.pitch, 0.0, 2.0) : 1.0,
    );
    setVolume(
      typeof voice?.volume === "number" ? clamp(voice.volume, 0.0, 1.0) : 1.0,
    );
  });

  const selectedVoice = createMemo(() => {
    const uri = selectedVoiceURI();
    if (!uri) return null;
    return voices().find((v) => v.voiceURI === uri) ?? null;
  });

  const speakSample = () => {
    if (!("speechSynthesis" in window)) {
      globalNotifications.addError(
        "SpeechSynthesis is not available on this device",
      );
      return;
    }
    window.speechSynthesis.cancel();

    const utterance = new window.SpeechSynthesisUtterance(sampleText());
    utterance.rate = rate();
    utterance.pitch = pitch();
    utterance.volume = volume();
    const voice = selectedVoice();
    if (voice) {
      utterance.voice = voice;
    }
    window.speechSynthesis.speak(utterance);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const payload: VoiceSetting | null = selectedVoiceURI()
        ? {
            voice_uri: selectedVoiceURI(),
            rate: rate(),
            pitch: pitch(),
            volume: volume(),
          }
        : null;

      await authAPI.updateProfile({
        settings: {
          voice_setting: payload as unknown as Record<string, unknown> | null,
        },
      });
      await refetch();
      globalNotifications.addSuccess("Voice settings saved");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to save voice settings";
      globalNotifications.addError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const supportsSpeech = createMemo(() => "speechSynthesis" in window);

  return (
    <SettingsPage
      heading="Voice"
      bottomLink={{ label: "Back to Settings", url: "/me/settings" }}
    >
      <div class="space-y-6">
        <div class="rounded-2xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
          <div class="space-y-1">
            <div class="text-xs uppercase tracking-wide text-stone-400">
              Kiosk voice
            </div>
            <p class="text-sm text-stone-600">
              Choose which voice is used when the kiosk reads notifications out
              loud.
            </p>
          </div>

          <Show
            when={supportsSpeech()}
            fallback={
              <div class="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                Speech synthesis isn’t available in this browser/device.
              </div>
            }
          >
            <div class="mt-5 grid gap-4">
              <label class="space-y-1">
                <div class="text-xs font-semibold text-stone-600">Voice</div>
                <select
                  class="w-full rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm"
                  value={selectedVoiceURI() ?? ""}
                  onChange={(e) =>
                    setSelectedVoiceURI(e.currentTarget.value || null)
                  }
                >
                  <option value="">Default (system)</option>
                  <For each={voices()}>
                    {(voice) => (
                      <option value={voice.voiceURI}>
                        {voice.name} ({voice.lang})
                      </option>
                    )}
                  </For>
                </select>
                <Show when={selectedVoice()}>
                  {(voice) => (
                    <div class="text-xs text-stone-400">
                      Selected: {voice().name} · {voice().lang}
                    </div>
                  )}
                </Show>
              </label>

              <div class="grid gap-4 sm:grid-cols-3">
                <label class="space-y-1">
                  <div class="text-xs font-semibold text-stone-600">Rate</div>
                  <input
                    type="range"
                    min="0.5"
                    max="2"
                    step="0.05"
                    value={rate()}
                    onInput={(e) => setRate(Number(e.currentTarget.value))}
                    class="w-full"
                  />
                  <div class="text-xs text-stone-400">{rate().toFixed(2)}</div>
                </label>

                <label class="space-y-1">
                  <div class="text-xs font-semibold text-stone-600">Pitch</div>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.05"
                    value={pitch()}
                    onInput={(e) => setPitch(Number(e.currentTarget.value))}
                    class="w-full"
                  />
                  <div class="text-xs text-stone-400">{pitch().toFixed(2)}</div>
                </label>

                <label class="space-y-1">
                  <div class="text-xs font-semibold text-stone-600">Volume</div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={volume()}
                    onInput={(e) => setVolume(Number(e.currentTarget.value))}
                    class="w-full"
                  />
                  <div class="text-xs text-stone-400">
                    {volume().toFixed(2)}
                  </div>
                </label>
              </div>

              <label class="space-y-1">
                <div class="text-xs font-semibold text-stone-600">
                  Sample text
                </div>
                <textarea
                  class="w-full rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm"
                  rows={3}
                  value={sampleText()}
                  onInput={(e) => setSampleText(e.currentTarget.value)}
                />
              </label>

              <div class="flex flex-col gap-2 sm:flex-row">
                <button
                  type="button"
                  onClick={speakSample}
                  class="rounded-full border border-stone-200 bg-white px-5 py-3 text-sm font-semibold text-stone-700 shadow-sm transition hover:border-stone-300 hover:text-stone-900"
                >
                  Play sample
                </button>
                <button
                  type="button"
                  disabled={isSaving()}
                  onClick={handleSave}
                  class="rounded-full bg-stone-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSaving() ? "Saving..." : "Save"}
                </button>
                <button
                  type="button"
                  onClick={() => navigate("/me/today/kiosk")}
                  class="rounded-full border border-amber-200 bg-amber-50 px-5 py-3 text-sm font-semibold text-amber-800 shadow-sm transition hover:bg-amber-100"
                >
                  Open kiosk
                </button>
              </div>
            </div>
          </Show>
        </div>
      </div>
    </SettingsPage>
  );
};

export default VoiceSettingsPage;
