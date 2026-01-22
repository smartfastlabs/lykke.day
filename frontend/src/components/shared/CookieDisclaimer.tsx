import { A, useLocation } from "@solidjs/router";
import { Show, createMemo, createSignal, onMount } from "solid-js";

const STORAGE_KEY = "lykke.cookie-consent";

const CookieDisclaimer = () => {
  const location = useLocation();
  const [consent, setConsent] = createSignal<string | null>(null);

  onMount(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setConsent(stored);
    }
  });

  const isPublicPage = createMemo(
    () => !location.pathname.startsWith("/me")
  );
  const shouldShow = createMemo(() => isPublicPage() && !consent());

  const handleChoice = (value: "accepted" | "essential"): void => {
    window.localStorage.setItem(STORAGE_KEY, value);
    setConsent(value);
  };

  return (
    <Show when={shouldShow()}>
      <div class="fixed inset-x-0 bottom-0 z-50 px-4 pb-4 sm:px-6">
        <div class="mx-auto max-w-3xl rounded-2xl border border-amber-100/80 bg-white/95 p-4 shadow-lg backdrop-blur">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div class="text-sm text-stone-600">
              <span class="font-medium text-stone-700">Cookies:</span> We use
              essential cookies to keep you signed in and optional cookies to
              improve your experience. Learn more in our{" "}
              <A
                href="/privacy"
                class="underline decoration-amber-300 underline-offset-2 hover:text-stone-800"
              >
                Privacy Policy
              </A>
              .
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <button
                class="min-w-[150px] rounded-full border border-amber-200 px-4 py-2 text-sm font-medium text-stone-600 transition hover:border-amber-300 hover:text-stone-800"
                type="button"
                onClick={() => handleChoice("essential")}
              >
                Essential only
              </button>
              <button
                class="min-w-[150px] rounded-full bg-amber-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-amber-600"
                type="button"
                onClick={() => handleChoice("accepted")}
              >
                Accept
              </button>
            </div>
          </div>
        </div>
      </div>
    </Show>
  );
};

export default CookieDisclaimer;
