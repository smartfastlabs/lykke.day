import type { Alarm } from "@/types/api";
import {
  createEffect,
  createMemo,
  createSignal,
  type Accessor,
} from "solid-js";

import { buildAlarmKey, buildYouTubeEmbedUrl } from "../kioskUtils";

export function useAlarmVideo(alarms: Accessor<Alarm[] | null | undefined>) {
  const [activeAlarm, setActiveAlarm] = createSignal<Alarm | null>(null);
  const [alarmVideoUrl, setAlarmVideoUrl] = createSignal<string | null>(null);
  const [lastAlarmKey, setLastAlarmKey] = createSignal<string | null>(null);
  const [fullscreenRequested, setFullscreenRequested] = createSignal(false);

  let fullscreenContainer: HTMLDivElement | undefined;
  const setFullscreenContainerRef = (el: HTMLDivElement) => {
    fullscreenContainer = el;
  };

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

  return {
    activeAlarm,
    alarmVideoUrl,
    setFullscreenContainerRef,
  };
}
