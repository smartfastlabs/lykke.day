import { onCleanup, onMount } from "solid-js";

const VERSION_URL = "/version.json";
const POLL_INTERVAL_MS = 60_000; // 1 minute

interface VersionPayload {
  buildId: string;
}

/**
 * Polls /version.json (written at build time). When the buildId changes
 * (new deploy), reloads the page so the kiosk picks up the new version.
 */
export function useDeployCheck(): void {
  onMount(() => {
    let initialBuildId: string | null = null;

    const check = async () => {
      try {
        const res = await fetch(VERSION_URL, {
          cache: "no-store",
          headers: { Accept: "application/json" },
        });
        if (!res.ok) return;
        const data = (await res.json()) as VersionPayload;
        const buildId = data?.buildId;
        if (typeof buildId !== "string") return;
        if (initialBuildId === null) {
          initialBuildId = buildId;
          return;
        }
        if (buildId !== initialBuildId) {
          window.location.reload();
        }
      } catch {
        // ignore network errors; will retry next interval
      }
    };

    const t = window.setInterval(check, POLL_INTERVAL_MS);
    check();

    onCleanup(() => {
      window.clearInterval(t);
    });
  });
}
