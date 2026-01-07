import { Component, Show, For, createSignal, onMount } from "solid-js";
import { Icon } from "solid-heroicons";
import { sun, arrowPath, calendar, bellAlert } from "solid-heroicons/outline";
import Footer from "@/components/shared/layout/footer";
import { marketingAPI } from "@/utils/api";

interface Feature {
  icon: typeof sun;
  title: string;
  description: string;
}

const Landing: Component = () => {
  const [contact, setContact] = createSignal("");
  const [showModal, setShowModal] = createSignal(false);
  const [submitted, setSubmitted] = createSignal(false);
  const [submitting, setSubmitting] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);
  const [mounted, setMounted] = createSignal(false);

  onMount(() => {
    setTimeout(() => setMounted(true), 50);
  });

  const handleOptIn = async () => {
    const value = contact().trim();
    if (!value) {
      setError("Please enter an email or phone number.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await marketingAPI.requestEarlyAccess(value);
      setShowModal(false);
      setSubmitted(true);
    } catch (err) {
      setError("Please enter a valid email or phone number.");
      console.error("Early access submission failed", err);
    } finally {
      setSubmitting(false);
    }
  };

  const features: Feature[] = [
    {
      icon: sun,
      title: "One Day at a Time",
      description:
        "No backlogs. No guilt. Just small, meaningful goals for today.",
    },
    {
      icon: arrowPath,
      title: "Gentle Routines",
      description:
        "Build rhythms that fit your life — not someone else's idea of productivity.",
    },
    {
      icon: calendar,
      title: "Calendar Aware",
      description:
        "We watch your calendar so wellness fits into your real life — not around it.",
    },
    {
      icon: bellAlert,
      title: "Soft Reminders",
      description:
        "Nudges, not nagging. We'll help you remember what matters to you.",
    },
  ];

  return (
    <Show
      when={submitted()}
      fallback={
        <div class="min-h-screen relative overflow-hidden">
          {/* Warm gradient background with subtle texture */}
          <div class="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50" />
          <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.15)_0%,_transparent_50%)]" />
          <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.1)_0%,_transparent_50%)]" />

          {/* Floating organic shapes */}
          <div class="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
          <div class="absolute bottom-32 left-10 w-48 h-48 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />
          <div class="absolute top-1/2 left-1/3 w-32 h-32 bg-gradient-to-r from-yellow-200/20 to-orange-200/20 rounded-full blur-2xl" />

          {/* Content */}
          <div class="relative z-10 flex flex-col items-center px-6 py-20 md:py-28">
            <div class="max-w-3xl w-full text-center">
              {/* Logo / Title */}
              <div
                class="mb-16 transition-all duration-1000 ease-out"
                style={{
                  opacity: mounted() ? 1 : 0,
                  transform: mounted() ? "translateY(0)" : "translateY(-20px)",
                }}
              >
                <h1 class="text-4xl md:text-4xl lg:text-8xl font-bold tracking-tight text-stone-800 mb-4">
                  lykke
                  <span class="text-amber-500">.</span>
                  day
                </h1>
              </div>

              {/* Definition card */}
              <div
                class="mb-10 transition-all duration-1000 delay-200 ease-out"
                style={{
                  opacity: mounted() ? 1 : 0,
                  transform: mounted() ? "translateY(0)" : "translateY(20px)",
                }}
              >
                <div class="inline-block bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl px-10 py-8 shadow-xl shadow-amber-900/5">
                  <p
                    class="text-stone-700 text-xl md:text-2xl italic leading-relaxed mb-3"
                    style={{
                      "font-family": "'Cormorant Garamond', Georgia, serif",
                    }}
                  >
                    Lykke{" "}
                    <span class="text-stone-400 not-italic text-lg">(n.)</span>{" "}
                    — the Danish art of finding happiness in everyday moments.
                  </p>
                  <p class="text-stone-400 text-sm tracking-wide uppercase">
                    pronounced: loo-kah
                  </p>
                </div>
              </div>

              {/* CTA Button */}
              <div
                class="my-16 transition-all duration-1000 delay-[400ms] ease-out"
                style={{
                  opacity: mounted() ? 1 : 0,
                  transform: mounted() ? "translateY(0)" : "translateY(20px)",
                }}
              >
                <button
                  onClick={() => setShowModal(true)}
                  class="group relative px-10 py-4 bg-gradient-to-r from-stone-800 to-stone-700 text-amber-50 rounded-xl hover:from-stone-700 hover:to-stone-600 transition-all duration-300 shadow-lg shadow-stone-900/20 hover:shadow-xl hover:shadow-stone-900/25 hover:-translate-y-0.5"
                >
                  <span class="relative z-10 font-medium tracking-wide">
                    Get early access
                  </span>
                  <div class="absolute inset-0 rounded-xl bg-gradient-to-r from-amber-400/20 to-orange-400/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </button>
              </div>

              {/* Tagline */}
              <p
                class="text-stone-500 text-base md:text-lg mb-8 max-w-md mx-auto leading-relaxed transition-all duration-1000 delay-300 ease-out"
                style={{
                  opacity: mounted() ? 1 : 0,
                  transform: mounted() ? "translateY(0)" : "translateY(20px)",
                }}
              >
                A daily companion app — not another endless task list. Just
                small intentions, gentle check-ins, and space to breathe.
              </p>

              {/* Features grid */}
              <div class="grid sm:grid-cols-2 gap-4 md:gap-6 mb-16">
                <For each={features}>
                  {(feature, index) => (
                    <div
                      class="group bg-white/50 backdrop-blur-sm border border-white/60 rounded-2xl p-6 md:p-7 text-left hover:bg-white/70 hover:shadow-lg hover:shadow-amber-900/5 transition-all duration-300 cursor-default"
                      style={{
                        opacity: mounted() ? 1 : 0,
                        transform: mounted()
                          ? "translateY(0)"
                          : "translateY(30px)",
                        transition: `all 0.8s ease-out ${0.5 + index() * 0.1}s`,
                      }}
                    >
                      <div class="flex items-start gap-4">
                        <div class="flex-shrink-0 w-11 h-11 rounded-xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center group-hover:from-amber-200 group-hover:to-orange-200 transition-colors duration-300">
                          <Icon
                            path={feature.icon}
                            class="w-5 h-5 text-amber-700"
                          />
                        </div>
                        <div class="flex-1 min-w-0">
                          <h3 class="text-stone-800 font-medium text-base mb-1.5 tracking-wide">
                            {feature.title}
                          </h3>
                          <p class="text-stone-500 text-sm leading-relaxed">
                            {feature.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </For>
              </div>

              {/* Inspirational quote */}
              <div
                class="max-w-xl mx-auto transition-all duration-1000 delay-[900ms] ease-out"
                style={{
                  opacity: mounted() ? 1 : 0,
                  transform: mounted() ? "translateY(0)" : "translateY(20px)",
                }}
              >
                <div class="relative py-8">
                  <div class="absolute left-0 top-0 w-8 h-8 border-l-2 border-t-2 border-amber-300/50" />
                  <div class="absolute right-0 bottom-0 w-8 h-8 border-r-2 border-b-2 border-amber-300/50" />
                  <p
                    class="text-stone-600 text-lg md:text-xl italic leading-relaxed px-6"
                    style={{
                      "font-family": "'Cormorant Garamond', Georgia, serif",
                    }}
                  >
                    "In an age of infinite distraction, the rarest gift you can
                    give yourself is a single, unhurried hour devoted to what
                    truly matters."
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div class="relative z-10">
            <Footer />
          </div>

          {/* Modal */}
          <Show when={showModal()}>
            <div
              class="fixed inset-0 z-50 flex items-center justify-center px-6"
              onClick={(e) =>
                e.target === e.currentTarget && setShowModal(false)
              }
            >
              <div class="absolute inset-0 bg-stone-900/40 backdrop-blur-sm" />
              <div class="relative bg-white/95 backdrop-blur-md rounded-2xl p-8 md:p-10 max-w-sm w-full text-center shadow-2xl shadow-stone-900/20 border border-white/50">
                {/* Decorative accent */}
                <div class="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center shadow-lg shadow-amber-900/10">
                  <Icon path={sun} class="w-6 h-6 text-amber-600" />
                </div>

                <h2
                  class="text-2xl text-stone-800 mb-3 mt-4"
                  style={{
                    "font-family": "'Cormorant Garamond', Georgia, serif",
                  }}
                >
                  Stay in the loop
                </h2>
                <p class="text-stone-500 text-sm mb-6 leading-relaxed">
                  Leave your email or phone and we'll let you know when
                  lykke.day is ready.
                </p>
                <input
                  type="text"
                  value={contact()}
                  onInput={(e) => {
                    setContact(e.currentTarget.value);
                    setError(null);
                  }}
                  placeholder="Email or phone"
                  class="w-full px-5 py-3.5 mb-4 bg-stone-50/80 border border-stone-200 rounded-xl text-stone-700 placeholder-stone-400 focus:outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100 transition-all duration-200"
                />
                <Show when={error()}>
                  <p class="text-rose-500 text-xs mb-3">{error()}</p>
                </Show>
                <p class="text-stone-400 text-xs mb-6">
                  We'll only reach out about lykke.day. Unsubscribe anytime.
                </p>
                <div class="flex gap-3">
                  <button
                    onClick={() => setShowModal(false)}
                    class="flex-1 py-3 border border-stone-200 text-stone-600 rounded-xl hover:bg-stone-50 hover:border-stone-300 transition-all duration-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleOptIn}
                    disabled={submitting()}
                    class="flex-1 py-3 bg-gradient-to-r from-stone-800 to-stone-700 text-white rounded-xl hover:from-stone-700 hover:to-stone-600 transition-all duration-200 shadow-md shadow-stone-900/20 disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {submitting() ? "Sending..." : "I'm in"}
                  </button>
                </div>
              </div>
            </div>
          </Show>
        </div>
      }
    >
      {/* Success state */}
      <div class="min-h-screen relative overflow-hidden flex flex-col items-center justify-center px-6">
        <div class="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50" />
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(251,191,36,0.15)_0%,_transparent_60%)]" />

        <div class="relative z-10 max-w-md text-center">
          <div class="w-16 h-16 mx-auto mb-8 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center shadow-lg shadow-amber-900/10">
            <Icon path={sun} class="w-8 h-8 text-amber-600" />
          </div>
          <p class="text-stone-700 text-xl mb-10 font-medium">
            We'll be in touch.
          </p>
          <div class="bg-white/60 backdrop-blur-sm border border-white/80 rounded-2xl px-8 py-6">
            <p
              class="text-stone-600 text-lg italic leading-relaxed"
              style={{
                "font-family": "'Cormorant Garamond', Georgia, serif",
              }}
            >
              "Happiness is not something ready made. It comes from your own
              actions."
            </p>
            <p class="text-stone-400 text-sm mt-3">— Dalai Lama</p>
          </div>
        </div>
      </div>
    </Show>
  );
};

export default Landing;
