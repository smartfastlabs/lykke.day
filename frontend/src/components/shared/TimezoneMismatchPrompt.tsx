import { Component, Show, createEffect, createMemo, createSignal } from "solid-js";
import { Portal } from "solid-js/web";

import { useAuth } from "@/providers/auth";
import { globalNotifications } from "@/providers/notifications";
import { authAPI } from "@/utils/api";

const DISMISSED_SIGNATURES_KEY = "lykke.timezonePrompt.dismissedSignatures.v1";
const MAX_DISMISSED_SIGNATURES = 10;

type LocalStorageLike = {
  getItem: (key: string) => string | null;
  setItem: (key: string, value: string) => void;
};

function getBrowserTimeZone(): string | null {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (typeof tz !== "string") return null;
    const trimmed = tz.trim();
    return trimmed.length > 0 ? trimmed : null;
  } catch {
    return null;
  }
}

function makeDismissSignature(params: {
  userId: string;
  currentUserTimezone: string | null;
  detectedTimezone: string;
}): string {
  const current = params.currentUserTimezone?.trim() || "null";
  return `${params.userId}:${current}:${params.detectedTimezone}`;
}

function getSafeLocalStorage(): LocalStorageLike | null {
  try {
    const storage = window.localStorage;
    if (!storage) return null;
    if (typeof storage.getItem !== "function") return null;
    if (typeof storage.setItem !== "function") return null;
    return storage as unknown as LocalStorageLike;
  } catch {
    return null;
  }
}

function readDismissedSignatures(): string[] {
  try {
    const storage = getSafeLocalStorage();
    if (!storage) return [];
    const raw = storage.getItem(DISMISSED_SIGNATURES_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((v): v is string => typeof v === "string");
  } catch {
    return [];
  }
}

function writeDismissedSignature(signature: string): void {
  const storage = getSafeLocalStorage();
  if (!storage) return;
  const existing = readDismissedSignatures();
  const next = [signature, ...existing.filter((s) => s !== signature)].slice(
    0,
    MAX_DISMISSED_SIGNATURES,
  );
  storage.setItem(DISMISSED_SIGNATURES_KEY, JSON.stringify(next));
}

const TimezoneMismatchPrompt: Component = () => {
  const { user, refetch } = useAuth();
  const [isOpen, setIsOpen] = createSignal(false);
  const [isSaving, setIsSaving] = createSignal(false);
  const [detectedTimezone, setDetectedTimezone] = createSignal<string | null>(null);

  const currentUserTimezone = createMemo(() => user()?.settings?.timezone ?? null);

  const mismatch = createMemo(() => {
    const detected = detectedTimezone();
    if (!detected) return null;
    const current = currentUserTimezone();
    if (!current) return detected;
    if (current.trim() === detected.trim()) return null;
    return detected;
  });

  const dismissSignature = createMemo(() => {
    const current = currentUserTimezone();
    const detected = detectedTimezone();
    const currentUser = user();
    if (!currentUser || !detected) return null;
    return makeDismissSignature({
      userId: currentUser.id,
      currentUserTimezone: current,
      detectedTimezone: detected,
    });
  });

  createEffect(() => {
    const currentUser = user();
    if (!currentUser) return;

    // Evaluate once per user load, but keep reactive to actual timezone changes.
    setDetectedTimezone(getBrowserTimeZone());

    const hasMismatch = Boolean(mismatch());
    if (!hasMismatch) {
      setIsOpen(false);
      return;
    }

    const signature = dismissSignature();
    if (!signature) return;
    const dismissed = readDismissedSignatures().includes(signature);
    if (!dismissed) setIsOpen(true);
  });

  const handleClose = () => {
    const signature = dismissSignature();
    if (signature) writeDismissedSignature(signature);
    setIsOpen(false);
  };

  const handleUpdateTimezone = async () => {
    const detected = mismatch();
    if (!detected) {
      setIsOpen(false);
      return;
    }

    setIsSaving(true);
    try {
      await authAPI.updateProfile({ settings: { timezone: detected } });
      await refetch();
      globalNotifications.addSuccess(`Timezone updated to ${detected}`);
      setIsOpen(false);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update timezone";
      globalNotifications.addError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const accountTimezoneLabel = createMemo(() => {
    const tz = currentUserTimezone();
    return tz && tz.trim().length > 0 ? tz : "not set";
  });

  return (
    <Show when={isOpen()}>
      <Portal>
        <div
          class="fixed inset-0 z-[60] flex items-center justify-center"
          onClick={handleClose}
        >
          <div class="absolute inset-0 bg-stone-900/45 backdrop-blur-[1px]" />
          <div
            class="relative w-full max-w-xl mx-auto px-6"
            onClick={(event) => event.stopPropagation()}
          >
            <div class="rounded-2xl border border-amber-100/80 bg-white/90 shadow-sm shadow-amber-900/10 backdrop-blur-sm p-6 sm:p-7 space-y-5">
              <div class="text-center space-y-2">
                <p class="text-xs sm:text-sm font-semibold uppercase tracking-[0.22em] text-amber-700">
                  New timezone detected
                </p>
              </div>

              <div class="flex flex-col gap-3 sm:flex-row sm:gap-4">
                <button
                  type="button"
                  onClick={handleUpdateTimezone}
                  disabled={isSaving()}
                  class="w-full rounded-full bg-amber-600 px-6 py-4 text-base sm:text-lg font-semibold text-white shadow-lg shadow-amber-900/15 transition hover:bg-amber-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200 disabled:cursor-not-allowed disabled:opacity-60"
                  aria-label={`Use timezone ${mismatch() ?? ""}`}
                >
                  {isSaving() ? "Updating..." : `Use ${mismatch() ?? ""}`}
                </button>
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isSaving()}
                  class="w-full rounded-full border border-stone-200 bg-white px-6 py-4 text-base sm:text-lg font-semibold text-stone-700 shadow-sm transition hover:bg-stone-50 hover:text-stone-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200 disabled:cursor-not-allowed disabled:opacity-60"
                  aria-label={`Keep account timezone ${accountTimezoneLabel()}`}
                >
                  {`Keep ${accountTimezoneLabel()}`}
                </button>
              </div>

              <p class="text-center text-sm sm:text-base text-stone-600">
                This affects how days, alarms, and “today” timing are computed.
              </p>
            </div>
          </div>
        </div>
      </Portal>
    </Show>
  );
};

export default TimezoneMismatchPrompt;

export const __test__ = {
  DISMISSED_SIGNATURES_KEY,
  getBrowserTimeZone,
  makeDismissSignature,
  readDismissedSignatures,
  writeDismissedSignature,
};

