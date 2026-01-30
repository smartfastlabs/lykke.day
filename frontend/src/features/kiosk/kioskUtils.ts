import type { Alarm, Event, Task } from "@/types/api";
import type { RoutineGroup } from "@/components/routines/RoutineGroupsList";

export interface KioskItem {
  label: string;
  time?: string | null;
  meta?: string | null;
}

export interface WeatherSnapshot {
  temperature: number;
  condition: string;
}

export const WEATHER_CODE_LABELS: Record<number, string> = {
  0: "Clear",
  1: "Mostly clear",
  2: "Partly cloudy",
  3: "Cloudy",
  45: "Fog",
  48: "Depositing rime fog",
  51: "Light drizzle",
  53: "Drizzle",
  55: "Heavy drizzle",
  61: "Light rain",
  63: "Rain",
  65: "Heavy rain",
  71: "Light snow",
  73: "Snow",
  75: "Heavy snow",
  80: "Rain showers",
  81: "Heavy showers",
  82: "Violent showers",
  95: "Thunderstorm",
};

export const normalizeTime = (time: string): string => time.slice(0, 5);

export const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));

export const isBenignSpeechSynthesisError = (error: unknown): boolean => {
  // Common, non-fatal errors when we intentionally call `speechSynthesis.cancel()`
  // or when a new utterance interrupts a previous one.
  if (typeof error !== "string") return false;
  const normalized = error.toLowerCase();
  return (
    normalized === "interrupted" ||
    normalized === "canceled" ||
    normalized === "cancelled"
  );
};

export const formatTimeString = (timeStr: string): string => {
  const [h, m] = normalizeTime(timeStr).split(":");
  const hour = parseInt(h, 10);
  const ampm = hour >= 12 ? "p" : "a";
  const hour12 = hour % 12 || 12;
  return `${hour12}:${m}${ampm}`;
};

export const formatClock = (date: Date): string =>
  date
    .toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    .toLowerCase()
    .replace(" ", "");

export const formatEventTime = (dateTimeStr: string): string =>
  new Date(dateTimeStr)
    .toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    .toLowerCase()
    .replace(" ", "");

export const formatRoutineTiming = (routine: RoutineGroup): string | null => {
  const status = routine.timing_status ?? "hidden";
  if (status === "active") return "active";
  if (status === "available") return "available";
  if (status === "past-due") return "past due";
  if (status === "inactive") {
    if (routine.next_available_time) {
      return `starts ${formatEventTime(routine.next_available_time)}`;
    }
    return "soon";
  }
  return null;
};

export const buildAlarmKey = (alarm: Alarm): string =>
  alarm.id?.trim() ||
  [alarm.name, alarm.time, alarm.type, alarm.url].filter(Boolean).join("|");

export const buildYouTubeEmbedUrl = (rawUrl: string): string | null => {
  try {
    const url = new URL(rawUrl);
    const host = url.hostname.replace(/^www\./, "");
    let videoId: string | null = null;

    if (host === "youtu.be") {
      videoId = url.pathname.replace("/", "") || null;
    } else if (host === "youtube.com" || host === "m.youtube.com") {
      if (url.pathname.startsWith("/watch")) {
        videoId = url.searchParams.get("v");
      } else if (url.pathname.startsWith("/embed/")) {
        videoId = url.pathname.split("/embed/")[1] || null;
      } else if (url.pathname.startsWith("/shorts/")) {
        videoId = url.pathname.split("/shorts/")[1] || null;
      }
    } else if (host === "youtube-nocookie.com") {
      videoId = url.pathname.split("/embed/")[1] || null;
    }

    if (!videoId) return null;

    const params = new URLSearchParams({
      autoplay: "1",
      playsinline: "1",
      controls: "1",
      rel: "0",
      modestbranding: "1",
      fs: "1",
    });

    return `https://www.youtube.com/embed/${videoId}?${params.toString()}`;
  } catch (error) {
    console.warn("Invalid alarm URL:", rawUrl, error);
    return null;
  }
};

export const getTaskTimeLabel = (task: Task): string | null => {
  const timeWindow = task.time_window;
  if (!timeWindow) return null;

  if (timeWindow.start_time && timeWindow.end_time) {
    return `${formatTimeString(timeWindow.start_time)}-${formatTimeString(
      timeWindow.end_time,
    )}`;
  }

  if (timeWindow.start_time) {
    return formatTimeString(timeWindow.start_time);
  }

  if (timeWindow.available_time) {
    return `after ${formatTimeString(timeWindow.available_time)}`;
  }

  if (timeWindow.end_time) {
    return `by ${formatTimeString(timeWindow.end_time)}`;
  }

  if (timeWindow.cutoff_time) {
    return `before ${formatTimeString(timeWindow.cutoff_time)}`;
  }

  return null;
};

export const isAllDayEvent = (event: Event): boolean => {
  const start = new Date(event.starts_at);
  const end = event.ends_at ? new Date(event.ends_at) : null;
  if (!end) return false;
  const diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
  return diffHours >= 23;
};
