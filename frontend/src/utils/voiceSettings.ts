export type DeviceVoiceSetting = {
  voice_uri: string | null;
  rate: number;
  pitch: number;
  volume: number;
};

const STORAGE_KEY = "lykke.voice_setting.v1";

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null;

export const loadDeviceVoiceSetting = (): DeviceVoiceSetting | null => {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;

    const parsed: unknown = JSON.parse(raw);
    if (!isRecord(parsed)) return null;

    const voiceURI =
      typeof parsed.voice_uri === "string" ? parsed.voice_uri : null;
    const rate =
      typeof parsed.rate === "number" ? clamp(parsed.rate, 0.5, 2.0) : 1.0;
    const pitch =
      typeof parsed.pitch === "number" ? clamp(parsed.pitch, 0.0, 2.0) : 1.0;
    const volume =
      typeof parsed.volume === "number" ? clamp(parsed.volume, 0.0, 1.0) : 1.0;

    return { voice_uri: voiceURI, rate, pitch, volume };
  } catch {
    return null;
  }
};

export const saveDeviceVoiceSetting = (setting: DeviceVoiceSetting | null) => {
  try {
    if (!setting) {
      window.localStorage.removeItem(STORAGE_KEY);
      return;
    }

    // Ensure stored values are already clamped/sane.
    const payload: DeviceVoiceSetting = {
      voice_uri:
        typeof setting.voice_uri === "string" ? setting.voice_uri : null,
      rate: clamp(setting.rate, 0.5, 2.0),
      pitch: clamp(setting.pitch, 0.0, 2.0),
      volume: clamp(setting.volume, 0.0, 1.0),
    };

    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Ignore (storage disabled / quota / non-browser contexts)
  }
};
