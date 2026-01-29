/* global URL, HTMLDivElement */
import {
  Component,
  For,
  JSX,
  Show,
  createEffect,
  createMemo,
  createSignal,
  onCleanup,
  onMount,
  untrack,
} from "solid-js";
import { Portal } from "solid-js/web";
import Page from "@/components/shared/layout/Page";
import { useStreamingData } from "@/providers/streamingData";
import { useAuth } from "@/providers/auth";
import { getDateString } from "@/utils/dates";
import { filterVisibleTasks } from "@/utils/tasks";
import {
  buildRoutineGroups,
  type RoutineGroup,
} from "@/components/routines/RoutineGroupsList";
import { dayAPI } from "@/utils/api";
import { globalNotifications } from "@/providers/notifications";
import type { Alarm, DayTemplate, Event, Reminder, Task } from "@/types/api";

type TimeBlock = NonNullable<DayTemplate["time_blocks"]>[number];

interface KioskItem {
  label: string;
  time?: string | null;
  meta?: string | null;
}

interface WeatherSnapshot {
  temperature: number;
  condition: string;
}

type UnlockState = "idle" | "attempting" | "enabled" | "failed";

const WEATHER_CODE_LABELS: Record<number, string> = {
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

const normalizeTime = (time: string): string => time.slice(0, 5);

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));

const formatTimeString = (timeStr: string): string => {
  const [h, m] = normalizeTime(timeStr).split(":");
  const hour = parseInt(h, 10);
  const ampm = hour >= 12 ? "p" : "a";
  const hour12 = hour % 12 || 12;
  return `${hour12}:${m}${ampm}`;
};

const formatClock = (date: Date): string =>
  date
    .toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    .toLowerCase()
    .replace(" ", "");

const formatEventTime = (dateTimeStr: string): string =>
  new Date(dateTimeStr)
    .toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    .toLowerCase()
    .replace(" ", "");

const formatRoutineTiming = (routine: RoutineGroup): string | null => {
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

const buildAlarmKey = (alarm: Alarm): string =>
  alarm.id?.trim() ||
  [alarm.name, alarm.time, alarm.type, alarm.url].filter(Boolean).join("|");

const buildYouTubeEmbedUrl = (rawUrl: string): string | null => {
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

const getTaskTimeLabel = (task: Task): string | null => {
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

const isAllDayEvent = (event: Event): boolean => {
  const start = new Date(event.starts_at);
  const end = event.ends_at ? new Date(event.ends_at) : null;
  if (!end) return false;
  const diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
  return diffHours >= 23;
};

const KioskPanel: Component<{
  title: string;
  count?: number;
  children: JSX.Element;
}> = (props) => (
  <div class="min-h-0 rounded-2xl border border-white/70 bg-white/80 p-3 shadow-sm shadow-amber-900/5 backdrop-blur-sm flex flex-col gap-2">
    <div class="flex items-center justify-between text-[11px] uppercase tracking-[0.25em] text-stone-500">
      <span>{props.title}</span>
      <Show when={props.count !== undefined}>
        <span class="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700">
          {props.count}
        </span>
      </Show>
    </div>
    <div class="flex-1 min-h-0 overflow-y-auto pr-1">{props.children}</div>
  </div>
);

const KioskList: Component<{
  items: KioskItem[];
  emptyLabel: string;
}> = (props) => (
  <Show
    when={props.items.length > 0}
    fallback={<p class="text-xs text-stone-400">No {props.emptyLabel}</p>}
  >
    <div class="space-y-1.5">
      <For each={props.items}>
        {(item) => (
          <div class="flex items-start gap-2 text-sm text-stone-800">
            <span class="w-14 flex-shrink-0 text-[11px] text-stone-500 tabular-nums text-right">
              {item.time ?? ""}
            </span>
            <span class="flex-1 min-w-0 truncate">{item.label}</span>
            <Show when={item.meta}>
              <span class="text-[10px] uppercase tracking-wide text-stone-400">
                {item.meta}
              </span>
            </Show>
          </div>
        )}
      </For>
    </div>
  </Show>
);

const KioskPage: Component = () => {
  const {
    dayContext,
    isLoading,
    day,
    tasks,
    events,
    reminders,
    routines,
    alarms,
    subscribeToTopic,
    isConnected,
  } = useStreamingData();
  const { user } = useAuth();
  const [now, setNow] = createSignal(new Date());
  const [weather, setWeather] = createSignal<WeatherSnapshot | null>(null);
  const [weatherError, setWeatherError] = createSignal(false);
  const [activeAlarm, setActiveAlarm] = createSignal<Alarm | null>(null);
  const [alarmVideoUrl, setAlarmVideoUrl] = createSignal<string | null>(null);
  const [lastAlarmKey, setLastAlarmKey] = createSignal<string | null>(null);
  const [fullscreenRequested, setFullscreenRequested] = createSignal(false);
  const [processedNotificationHashes, setProcessedNotificationHashes] =
    createSignal<Set<string>>(new Set());
  const [isSendingTest, setIsSendingTest] = createSignal(false);
  const [ttsSupported, setTtsSupported] = createSignal(false);
  const [speechUnlocked, setSpeechUnlocked] = createSignal(false);
  const [voices, setVoices] = createSignal<SpeechSynthesisVoice[]>([]);
  const [unlockState, setUnlockState] = createSignal<UnlockState>("idle");
  const [queuedKioskMessages, setQueuedKioskMessages] = createSignal<string[]>(
    [],
  );
  const [lastKioskMessage, setLastKioskMessage] = createSignal<{
    message: string;
    created_at?: string;
    triggered_by?: string | null;
  } | null>(null);
  const [ttsLastError, setTtsLastError] = createSignal<string | null>(null);
  let fullscreenContainer: HTMLDivElement | undefined;

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
        setTtsLastError(
          typeof (event as unknown as { error?: unknown }).error === "string"
            ? String((event as unknown as { error?: unknown }).error)
            : "Speech synthesis failed to start",
        );
      };
      window.speechSynthesis.speak(utterance);

      // If nothing starts shortly, mark as failed (helps on devices that silently no-op).
      window.setTimeout(() => {
        if (!speechUnlocked()) {
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
        setTtsLastError(
          typeof (event as unknown as { error?: unknown }).error === "string"
            ? String((event as unknown as { error?: unknown }).error)
            : "Speech synthesis error",
        );
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
    const voiceSetting = (
      untrack(() => user())?.settings as { voice_setting?: unknown } | undefined
    )?.voice_setting as
      | {
          voice_uri?: string | null;
          rate?: number | null;
          pitch?: number | null;
          volume?: number | null;
        }
      | null
      | undefined;

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
      setTtsLastError(
        typeof (event as unknown as { error?: unknown }).error === "string"
          ? String((event as unknown as { error?: unknown }).error)
          : "Speech synthesis error",
      );
    };
    utterance.onend = () => {
      // Continue draining the queue
      queueMicrotask(() => speakQueuedMessages());
    };

    setTtsLastError(null);
    window.speechSynthesis.speak(utterance);
  };

  const enqueueKioskMessage = (message: string) => {
    setQueuedKioskMessages((prev) => [...prev, message]);
    // Attempt immediate playback (will no-op if not unlocked)
    speakQueuedMessages();
  };

  const handleSendTestNotification = async () => {
    setIsSendingTest(true);
    try {
      // Ensure this click also unlocks speech on devices that require gestures.
      unlockSpeech();
      await dayAPI.sendTestKioskNotification();
      globalNotifications.addInfo("Test notification sent", { duration: 3000 });
    } catch (error) {
      console.error("Failed to send test notification:", error);
      globalNotifications.addError("Failed to send test notification");
    } finally {
      setIsSendingTest(false);
    }
  };

  onMount(() => {
    setTtsSupported("speechSynthesis" in window);

    if ("speechSynthesis" in window) {
      loadVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        loadVoices();
      };
    }

    const interval = setInterval(() => {
      setNow(new Date());
    }, 30000);

    onCleanup(() => {
      clearInterval(interval);
    });
  });

  onMount(() => {
    if (!("geolocation" in navigator)) {
      setWeatherError(true);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const url = new window.URL("https://api.open-meteo.com/v1/forecast");
          url.searchParams.set("latitude", latitude.toString());
          url.searchParams.set("longitude", longitude.toString());
          url.searchParams.set("current_weather", "true");
          url.searchParams.set("temperature_unit", "fahrenheit");

          const response = await fetch(url.toString());
          if (!response.ok) {
            setWeatherError(true);
            return;
          }

          const data = (await response.json()) as {
            current_weather?: { temperature: number; weathercode: number };
          };

          if (!data.current_weather) {
            setWeatherError(true);
            return;
          }

          setWeather({
            temperature: Math.round(data.current_weather.temperature),
            condition:
              WEATHER_CODE_LABELS[data.current_weather.weathercode] ??
              "Weather",
          });
        } catch (error) {
          console.error("Weather lookup failed:", error);
          setWeatherError(true);
        }
      },
      () => {
        setWeatherError(true);
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 30 * 60 * 1000 },
    );
  });

  // Subscribe to kiosk notification events and handle TTS
  createEffect(() => {
    // Unlock on any user interaction (click, touch, keypress)
    const unlockEvents = ["click", "touchstart", "keydown"];
    const cleanupUnlockListeners: (() => void)[] = [];
    unlockEvents.forEach((eventType) => {
      document.addEventListener(eventType, unlockSpeech, {
        once: true,
        passive: true,
      });
      // Note: Since we use { once: true }, the listener auto-removes after first call
      // But we track it for completeness
      cleanupUnlockListeners.push(() => {
        document.removeEventListener(eventType, unlockSpeech);
      });
    });

    const unsubscribe = subscribeToTopic("KioskNotificationEvent", (event) => {
      const payload = event.event_data as {
        message?: string;
        category?: string;
        message_hash?: string;
        created_at?: string;
        triggered_by?: string | null;
      };

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

      if (!speechUnlocked()) {
        console.log(
          "Kiosk notification received, but audio is locked. Waiting for user interaction to enable speech.",
        );
      }

      enqueueKioskMessage(payload.message);
    });

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

  const date = createMemo(() => {
    const dayValue = day();
    if (!dayValue) return new Date();

    const [year, month, dayNum] = dayValue.date.split("-").map(Number);
    return new Date(year, month - 1, dayNum);
  });

  const weekday = createMemo(() =>
    new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(date()),
  );

  const monthDay = createMemo(() =>
    new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
    }).format(date()),
  );

  const dateLabel = createMemo(() => `${weekday()} ${monthDay()}`);
  const planTitle = createMemo(
    () => day()?.high_level_plan?.title?.trim() ?? "",
  );
  const isWorkday = createMemo(() => Boolean(day()?.tags?.includes("WORKDAY")));
  const timeBlocks = createMemo<TimeBlock[]>(
    () => day()?.template?.time_blocks ?? [],
  );
  const dayDate = createMemo(() => day()?.date ?? getDateString());
  const isToday = createMemo(() => dayDate() === getDateString());

  const blocks = createMemo(() =>
    timeBlocks()
      .map((block) => {
        const start =
          Number(block.start_time.slice(0, 2)) * 60 +
          Number(block.start_time.slice(3, 5));
        const end = Math.max(
          Number(block.end_time.slice(0, 2)) * 60 +
            Number(block.end_time.slice(3, 5)),
          start + 1,
        );
        return { ...block, start, end };
      })
      .sort((a, b) => a.start - b.start),
  );

  const currentBlock = createMemo(() => {
    if (!isToday()) return null;
    const nowMinutes = now().getHours() * 60 + now().getMinutes();
    return blocks().find(
      (block) => nowMinutes >= block.start && nowMinutes < block.end,
    );
  });

  const nextBlock = createMemo(() => {
    const items = blocks();
    if (items.length === 0) return null;
    if (!isToday()) return items[0];
    const nowMinutes = now().getHours() * 60 + now().getMinutes();
    return items.find((block) => block.start > nowMinutes) ?? null;
  });

  const allTasks = createMemo(() => tasks() ?? []);
  const allEvents = createMemo(() => events() ?? []);
  const allReminders = createMemo(() => reminders() ?? []);
  const allRoutines = createMemo(() => routines() ?? []);
  const activeReminders = createMemo(() =>
    allReminders().filter((reminder) => reminder.status === "INCOMPLETE"),
  );
  const visibleTasks = createMemo(() => filterVisibleTasks(allTasks()));
  const activeTasks = createMemo(() =>
    visibleTasks().filter(
      (task) => task.status !== "COMPLETE" && task.status !== "PUNT",
    ),
  );
  const upcomingTaskCandidates = createMemo(() =>
    allTasks().filter((task) => task.timing_status === "inactive"),
  );

  const rightNowEventIds = createMemo(() => {
    const currentTime = now();
    return new Set(
      allEvents()
        .filter((event) => {
          if (isAllDayEvent(event)) return false;
          const start = new Date(event.starts_at);
          const end = event.ends_at ? new Date(event.ends_at) : null;
          return start <= currentTime && (!end || end >= currentTime);
        })
        .map((event) => event.id)
        .filter((id): id is string => Boolean(id)),
    );
  });

  const upcomingEventIds = createMemo(() => {
    const currentTime = now();
    const windowEnd = new Date(currentTime.getTime() + 1000 * 30 * 60);
    return new Set(
      allEvents()
        .filter((event) => {
          if (isAllDayEvent(event)) return false;
          const start = new Date(event.starts_at);
          const end = event.ends_at ? new Date(event.ends_at) : null;
          if (start <= currentTime && (!end || end >= currentTime)) {
            return false;
          }
          return start >= currentTime && start <= windowEnd;
        })
        .map((event) => event.id)
        .filter((id): id is string => Boolean(id)),
    );
  });

  const rightNowTaskIds = createMemo(() => {
    return new Set(
      activeTasks()
        .filter((task) => task.timing_status === "past-due")
        .map((task) => task.id)
        .filter((id): id is string => Boolean(id)),
    );
  });

  const upcomingTaskIds = createMemo(() => {
    return new Set(
      upcomingTaskCandidates()
        .map((task) => task.id)
        .filter((id): id is string => Boolean(id)),
    );
  });

  const eventsForSections = createMemo(() => {
    const ids = new Set<string>();
    rightNowEventIds().forEach((id) => ids.add(id));
    upcomingEventIds().forEach((id) => ids.add(id));
    return allEvents().filter((event) => {
      const eventId = event.id;
      if (!eventId) return true;
      return !ids.has(eventId);
    });
  });

  const tasksForSections = createMemo(() => {
    const ids = new Set<string>();
    rightNowTaskIds().forEach((id) => ids.add(id));
    upcomingTaskIds().forEach((id) => ids.add(id));
    return filterVisibleTasks(allTasks()).filter((task) => {
      const taskId = task.id;
      if (!taskId) return true;
      if (ids.has(taskId)) return false;
      return true;
    });
  });

  const rightNowItems = createMemo<KioskItem[]>(() => {
    const items: KioskItem[] = [];
    const currentTime = now();

    allEvents()
      .filter((event) => {
        if (isAllDayEvent(event)) return false;
        const start = new Date(event.starts_at);
        const end = event.ends_at ? new Date(event.ends_at) : null;
        return start <= currentTime && (!end || end >= currentTime);
      })
      .forEach((event) => {
        items.push({
          label: event.name ?? "Event",
          time: formatEventTime(event.starts_at),
          meta: "event",
        });
      });

    activeTasks()
      .filter((task) => task.timing_status === "past-due")
      .forEach((task) => {
        items.push({
          label: task.name
            .replace("ROUTINE DEFINITION: ", "")
            .replace("Routine Definition: ", ""),
          time: getTaskTimeLabel(task),
          meta: "task",
        });
      });

    return items;
  });

  const upcomingItems = createMemo<KioskItem[]>(() => {
    const items: KioskItem[] = [];
    const currentTime = now();
    const windowEnd = new Date(currentTime.getTime() + 1000 * 30 * 60);

    allEvents()
      .filter((event) => {
        if (isAllDayEvent(event)) return false;
        const start = new Date(event.starts_at);
        if (start < currentTime || start > windowEnd) return false;
        return true;
      })
      .forEach((event) => {
        items.push({
          label: event.name ?? "Event",
          time: formatEventTime(event.starts_at),
          meta: "event",
        });
      });

    upcomingTaskCandidates().forEach((task) => {
      items.push({
        label: task.name
          .replace("ROUTINE DEFINITION: ", "")
          .replace("Routine Definition: ", ""),
        time: getTaskTimeLabel(task),
        meta: "task",
      });
    });

    return items;
  });

  const eventItems = createMemo<KioskItem[]>(() => {
    const items = eventsForSections()
      .slice()
      .sort(
        (a, b) =>
          new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
      )
      .map((event) => ({
        label: event.name ?? "Event",
        time: isAllDayEvent(event)
          ? "all day"
          : formatEventTime(event.starts_at),
        meta: event.category?.toLowerCase().replace("_", " "),
      }));

    return items;
  });

  const taskItems = createMemo<KioskItem[]>(() =>
    tasksForSections()
      .filter((task) => task.status !== "COMPLETE" && task.status !== "PUNT")
      .map((task) => ({
        label: task.name
          .replace("ROUTINE DEFINITION: ", "")
          .replace("Routine Definition: ", ""),
        time: getTaskTimeLabel(task),
        meta: task.type?.toLowerCase().replace("_", " "),
      })),
  );

  const reminderItems = createMemo<KioskItem[]>(() =>
    activeReminders().map((reminder: Reminder) => ({
      label: reminder.name,
      meta: "reminder",
    })),
  );

  const routineItems = createMemo<KioskItem[]>(() => {
    const groups = buildRoutineGroups(activeTasks(), allRoutines());
    return groups.map((group) => ({
      label: group.routineName ?? "Routine",
      time: formatRoutineTiming(group),
      meta: `${group.pendingCount}/${group.totalCount}`,
    }));
  });

  const timeLabel = createMemo(() => formatClock(now()));

  const triggeredAlarm = createMemo<Alarm | null>(() => {
    const active = (alarms() ?? []).filter(
      (alarm) => (alarm.status ?? "ACTIVE") === "TRIGGERED",
    );
    if (active.length === 0) return null;
    return [...active].sort((a, b) => {
      const aTime = a.datetime
        ? new Date(a.datetime).getTime()
        : Number.MAX_SAFE_INTEGER;
      const bTime = b.datetime
        ? new Date(b.datetime).getTime()
        : Number.MAX_SAFE_INTEGER;
      return aTime - bTime;
    })[0];
  });

  createEffect(() => {
    const alarm = triggeredAlarm();
    if (!alarm) {
      setActiveAlarm(null);
      setAlarmVideoUrl(null);
      setLastAlarmKey(null);
      setFullscreenRequested(false);
      return;
    }

    const alarmKey = buildAlarmKey(alarm);
    if (alarmKey === lastAlarmKey()) {
      return;
    }

    setLastAlarmKey(alarmKey);

    if (alarm.type === "URL" && alarm.url) {
      const embedUrl = buildYouTubeEmbedUrl(alarm.url);
      if (embedUrl) {
        setActiveAlarm(alarm);
        setAlarmVideoUrl(embedUrl);
      } else {
        window.location.assign(alarm.url);
      }
      return;
    }

    setActiveAlarm(alarm);
    setAlarmVideoUrl(null);
  });

  createEffect(() => {
    if (!alarmVideoUrl() || !fullscreenContainer || fullscreenRequested()) {
      return;
    }
    if (fullscreenContainer.requestFullscreen) {
      const request = fullscreenContainer.requestFullscreen();
      if (request && typeof request.then === "function") {
        request.catch((error: unknown) => {
          console.warn("Unable to enter fullscreen:", error);
        });
      }
    } else {
      const legacy = fullscreenContainer as HTMLDivElement & {
        webkitRequestFullscreen?: () => void;
      };
      legacy.webkitRequestFullscreen?.();
    }
    setFullscreenRequested(true);
  });

  return (
    <Page variant="app" hideFooter hideFloatingButtons>
      <div class="min-h-[100dvh] h-[100dvh] box-border relative overflow-hidden">
        <Show when={activeAlarm() && alarmVideoUrl()}>
          <Portal>
            <div
              ref={fullscreenContainer}
              class="fixed inset-0 z-[90] bg-black"
            >
              <iframe
                class="h-full w-full"
                src={alarmVideoUrl() ?? ""}
                title={activeAlarm()?.name ?? "Alarm Video"}
                allow="autoplay; fullscreen"
                allowfullscreen
              />
            </div>
          </Portal>
        </Show>
        <Show
          when={!isLoading() && dayContext()}
          fallback={
            <div class="relative z-10 p-8 text-center text-stone-400">
              Loading...
            </div>
          }
        >
          <div class="relative z-10 h-full w-full">
            <div class="h-full w-full flex flex-col gap-3 p-[25px]">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm uppercase tracking-[0.3em] text-stone-500">
                    {dateLabel()}
                  </p>
                  <p class="text-2xl font-semibold text-stone-800">
                    {planTitle() || "Today"}
                  </p>
                  <div class="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-stone-500">
                    <span
                      class={
                        isConnected()
                          ? "rounded-full bg-emerald-50 px-2 py-0.5 font-semibold text-emerald-700"
                          : "rounded-full bg-rose-50 px-2 py-0.5 font-semibold text-rose-700"
                      }
                    >
                      {isConnected() ? "WS connected" : "WS disconnected"}
                    </span>
                    <Show when={ttsSupported()}>
                      <span
                        class={
                          speechUnlocked()
                            ? "rounded-full bg-emerald-50 px-2 py-0.5 font-semibold text-emerald-700"
                            : "rounded-full bg-amber-50 px-2 py-0.5 font-semibold text-amber-700"
                        }
                      >
                        {speechUnlocked() ? "Audio enabled" : "Audio locked"}
                      </span>
                      <span class="rounded-full bg-stone-100 px-2 py-0.5 font-semibold text-stone-600">
                        {voices().length} voices
                      </span>
                      <Show
                        when={!speechUnlocked() && unlockState() !== "idle"}
                      >
                        <span
                          class={
                            unlockState() === "attempting"
                              ? "rounded-full bg-amber-50 px-2 py-0.5 font-semibold text-amber-700"
                              : unlockState() === "failed"
                                ? "rounded-full bg-rose-50 px-2 py-0.5 font-semibold text-rose-700"
                                : "rounded-full bg-emerald-50 px-2 py-0.5 font-semibold text-emerald-700"
                          }
                        >
                          {unlockState() === "attempting"
                            ? "Enabling…"
                            : unlockState() === "failed"
                              ? "Enable failed"
                              : "Enabled"}
                        </span>
                      </Show>
                    </Show>
                    <Show when={!ttsSupported()}>
                      <span class="rounded-full bg-rose-50 px-2 py-0.5 font-semibold text-rose-700">
                        No SpeechSynthesis
                      </span>
                    </Show>
                    <Show when={queuedKioskMessages().length > 0}>
                      <span class="rounded-full bg-amber-50 px-2 py-0.5 font-semibold text-amber-700">
                        {queuedKioskMessages().length} queued
                      </span>
                    </Show>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <Show when={ttsSupported() && !speechUnlocked()}>
                    <button
                      onClick={() => {
                        unlockSpeech();
                        speakQueuedMessages();
                      }}
                      class="rounded-lg bg-stone-900 px-4 py-2 text-sm font-medium text-white hover:bg-stone-800 transition-colors"
                    >
                      Enable audio
                    </button>
                  </Show>
                  <Show when={ttsSupported()}>
                    <button
                      onClick={() => {
                        unlockSpeech();
                        speakSample();
                      }}
                      class="rounded-lg bg-white/80 px-4 py-2 text-sm font-medium text-stone-800 hover:bg-white transition-colors border border-white/70"
                    >
                      Play sample
                    </button>
                  </Show>
                  <button
                    onClick={handleSendTestNotification}
                    disabled={isSendingTest()}
                    class="rounded-lg bg-amber-100 px-4 py-2 text-sm font-medium text-amber-800 hover:bg-amber-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isSendingTest() ? "Sending..." : "Test Notification"}
                  </button>
                </div>
              </div>
              <Show when={ttsLastError()}>
                <div class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-800">
                  TTS error: {ttsLastError()}
                </div>
              </Show>
              <Show when={lastKioskMessage()}>
                {(msg) => (
                  <div class="rounded-xl border border-white/70 bg-white/70 px-4 py-2 text-sm text-stone-700">
                    <span class="text-xs uppercase tracking-[0.2em] text-stone-400">
                      Last kiosk notification
                    </span>
                    <div class="mt-1 flex flex-wrap items-center gap-2">
                      <span class="font-medium text-stone-800">
                        {msg().message}
                      </span>
                      <Show when={msg().triggered_by}>
                        <span class="rounded-full bg-stone-100 px-2 py-0.5 text-[11px] font-semibold text-stone-600">
                          {msg().triggered_by}
                        </span>
                      </Show>
                      <Show when={msg().created_at}>
                        <span class="text-[11px] text-stone-500 tabular-nums">
                          {msg().created_at}
                        </span>
                      </Show>
                    </div>
                  </div>
                )}
              </Show>
              <div class="flex-1 min-h-0 grid grid-cols-3 grid-rows-2 gap-3">
                <KioskPanel title="Now" count={rightNowItems().length}>
                  <div class="space-y-3">
                    <div class="flex items-end justify-between">
                      <div class="text-4xl font-semibold text-amber-700 tabular-nums">
                        {timeLabel()}
                      </div>
                    </div>
                    <Show when={isWorkday()}>
                      <span class="inline-flex items-center rounded-full bg-amber-50/95 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-amber-600 shadow-sm shadow-amber-900/5">
                        Workday
                      </span>
                    </Show>
                    <div class="flex items-center justify-between rounded-xl bg-white/70 px-3 py-2 text-sm text-stone-700">
                      <div>
                        <p class="text-[11px] uppercase tracking-[0.2em] text-stone-400">
                          Weather
                        </p>
                        <Show
                          when={weather()}
                          fallback={
                            <p class="text-sm text-stone-500">
                              {weatherError() ? "Unavailable" : "Loading..."}
                            </p>
                          }
                        >
                          {(snapshot) => (
                            <p class="text-base font-semibold text-stone-800">
                              {snapshot().temperature}°F ·{" "}
                              {snapshot().condition}
                            </p>
                          )}
                        </Show>
                      </div>
                      <div class="text-2xl">⛅️</div>
                    </div>
                    <Show when={blocks().length > 0}>
                      <div class="text-[11px] text-stone-500">
                        <Show
                          when={currentBlock()}
                          fallback={
                            <span>
                              <span class="font-medium">Current:</span> none
                            </span>
                          }
                        >
                          {(block) => (
                            <span>
                              <span class="font-medium">Current:</span>{" "}
                              {block().name}
                            </span>
                          )}
                        </Show>
                        <span class="mx-2 text-stone-300">•</span>
                        <Show
                          when={nextBlock()}
                          fallback={
                            <span>
                              <span class="font-medium">Next:</span> none
                            </span>
                          }
                        >
                          {(block) => (
                            <span>
                              <span class="font-medium">Next:</span>{" "}
                              {block().name}
                            </span>
                          )}
                        </Show>
                      </div>
                    </Show>
                    <KioskList
                      items={rightNowItems()}
                      emptyLabel="active items"
                    />
                  </div>
                </KioskPanel>
                <KioskPanel
                  title="Upcoming (30m)"
                  count={upcomingItems().length}
                >
                  <KioskList
                    items={upcomingItems()}
                    emptyLabel="upcoming items"
                  />
                </KioskPanel>
                <KioskPanel title="Reminders" count={activeReminders().length}>
                  <KioskList items={reminderItems()} emptyLabel="reminders" />
                </KioskPanel>
                <KioskPanel title="Events" count={eventItems().length}>
                  <KioskList items={eventItems()} emptyLabel="events" />
                </KioskPanel>
                <KioskPanel title="Tasks" count={taskItems().length}>
                  <KioskList items={taskItems()} emptyLabel="tasks" />
                </KioskPanel>
                <KioskPanel title="Routines" count={routineItems().length}>
                  <KioskList items={routineItems()} emptyLabel="routines" />
                </KioskPanel>
              </div>
            </div>
          </div>
        </Show>
      </div>
    </Page>
  );
};

export default KioskPage;
