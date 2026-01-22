import { Icon } from "solid-heroicons";
import {
  sparkles,
  shieldCheck,
  heart,
} from "solid-heroicons/outline";
import { Component, Show, createSignal, onCleanup, onMount, For } from "solid-js";
import SEO from "@/components/shared/SEO";
import ModalPage from "@/components/shared/ModalPage";

type InstallOutcome = "idle" | "prompting" | "accepted" | "dismissed";
type PlatformType = "ios" | "android" | "desktop" | "unknown";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
};

const highlights = [
  {
    icon: sparkles,
    title: "Gentle daily rhythm",
    description: "Plan one day at a time with soft reminders and calm structure.",
  },
  {
    icon: heart,
    title: "Designed for real life",
    description: "Routines that flex with your calendar, not fight it.",
  },
  {
    icon: shieldCheck,
    title: "Private by default",
    description: "Your data stays yours. No ads, no trackers, no noise.",
  },
];

const Install: Component = () => {
  const [isInstallable, setIsInstallable] = createSignal(false);
  const [isInstalled, setIsInstalled] = createSignal(false);
  const [installState, setInstallState] = createSignal<InstallOutcome>("idle");
  const [platform, setPlatform] = createSignal<PlatformType>("unknown");
  let deferredPrompt: BeforeInstallPromptEvent | null = null;

  const detectPlatform = (): PlatformType => {
    const ua = navigator.userAgent.toLowerCase();
    if (/iphone|ipad|ipod/.test(ua)) return "ios";
    if (/android/.test(ua)) return "android";
    if (/mac|win|linux/.test(ua)) return "desktop";
    return "unknown";
  };

  const detectInstalled = (): void => {
    const displayModeStandalone = window.matchMedia("(display-mode: standalone)").matches;
    const iosStandalone = Boolean((navigator as Navigator & { standalone?: boolean }).standalone);
    setIsInstalled(displayModeStandalone || iosStandalone);
  };

  const handleInstall = async (): Promise<void> => {
    if (!deferredPrompt) return;
    setInstallState("prompting");
    try {
      await deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      setInstallState(choice.outcome === "accepted" ? "accepted" : "dismissed");
      if (choice.outcome === "accepted") {
        setIsInstalled(true);
      }
    } catch (error) {
      console.error("PWA install prompt failed:", error);
      setInstallState("dismissed");
    } finally {
      deferredPrompt = null;
      setIsInstallable(false);
    }
  };

  onMount(() => {
    setPlatform(detectPlatform());
    detectInstalled();

    const displayModeQuery = window.matchMedia("(display-mode: standalone)");
    const handleDisplayModeChange = () => detectInstalled();

    if (displayModeQuery.addEventListener) {
      displayModeQuery.addEventListener("change", handleDisplayModeChange);
    } else {
      displayModeQuery.addListener(handleDisplayModeChange);
    }

    const handleBeforeInstall = (event: Event): void => {
      event.preventDefault();
      deferredPrompt = event as BeforeInstallPromptEvent;
      setIsInstallable(true);
    };

    const handleAppInstalled = (): void => {
      setIsInstalled(true);
      setIsInstallable(false);
      setInstallState("accepted");
      deferredPrompt = null;
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstall);
    window.addEventListener("appinstalled", handleAppInstalled);

    onCleanup(() => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
      window.removeEventListener("appinstalled", handleAppInstalled);
      if (displayModeQuery.removeEventListener) {
        displayModeQuery.removeEventListener("change", handleDisplayModeChange);
      } else {
        displayModeQuery.removeListener(handleDisplayModeChange);
      }
    });
  });

  const installButtonLabel = () => {
    if (isInstalled()) return "Installed";
    if (isInstallable()) return "Install";
    if (platform() === "ios") return "Add to Home Screen";
    return "Install";
  };

  return (
    <>
      <SEO
        title="Install lykke.day"
        description="Install lykke.day as a PWA for a calm, app-like experience. Quick, private, and built for gentle daily rhythms."
        path="/install"
      />
      <ModalPage subtitle="Install the app for a calm, offline-ready day.">
        <div class="space-y-6">
          <div class="text-center space-y-3">
            <img
              src="/icons/icon-192x192.png"
              alt="lykke.day app icon"
              class="w-16 h-16 mx-auto"
              loading="lazy"
            />
            <div>
              <p class="text-xs uppercase tracking-[0.35em] text-amber-500">
                PWA install
              </p>
              <p class="text-lg font-semibold text-stone-800 mt-2">
                Install lykke.day
              </p>
              <p class="text-stone-500 text-sm mt-2">
                A calm, one-day-at-a-time companion.
              </p>
            </div>
          </div>

          <div class="flex flex-col gap-3">
            <button
              class="group relative inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r from-stone-800 to-stone-700 text-amber-50 rounded-xl hover:from-stone-700 hover:to-stone-600 transition-all duration-300 shadow-lg shadow-stone-900/15 disabled:opacity-60 disabled:cursor-not-allowed"
              onClick={handleInstall}
              disabled={isInstalled()}
            >
              <span class="relative z-10 font-medium tracking-wide">
                {installButtonLabel()}
              </span>
              <div class="absolute inset-0 rounded-xl bg-gradient-to-r from-amber-400/20 to-orange-400/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </button>
          </div>

          <Show when={isInstalled()}>
            <div class="text-sm text-emerald-600 font-medium text-center">
              Installed on this device.
            </div>
          </Show>
          <Show when={installState() === "dismissed"}>
            <div class="text-sm text-stone-500 text-center">
              Install dismissed — you can try again anytime.
            </div>
          </Show>

          <div class="grid gap-4">
            <For each={highlights}>
              {(item) => (
                <div class="bg-white/70 border border-white/80 rounded-2xl p-4">
                  <div class="flex items-start gap-3">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center">
                      <Icon path={item.icon} class="w-5 h-5 text-amber-700" />
                    </div>
                    <div>
                      <h3 class="text-stone-800 font-semibold text-sm mb-1">
                        {item.title}
                      </h3>
                      <p class="text-stone-500 text-xs leading-relaxed">
                        {item.description}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </For>
          </div>
        </div>
      </ModalPage>
    </>
  );
};

export default Install;
