import { Component, For } from "solid-js";
import { A } from "@solidjs/router";
import { Icon } from "solid-heroicons";
import {
  sun,
  arrowPath,
  calendar,
  bellAlert,
  heart,
  sparkles,
  xCircle,
} from "solid-heroicons/outline";
import Footer from "@/components/shared/layout/Footer";
import SEO from "@/components/shared/SEO";
import { useAuth } from "@/providers/auth";
import { usePageAnimation } from "@/utils/navigation";

interface Feature {
  icon: typeof sun;
  title: string;
  description: string;
}

const Landing: Component = () => {
  const { isAuthenticated } = useAuth();
  const mounted = usePageAnimation("landing");

  const AccountLink: Component = () => (
    <a
      href={isAuthenticated() ? "/me/today" : "/login"}
      class="absolute top-6 right-6 z-20 px-4 py-2 rounded-full bg-white/80 border border-stone-200 text-sm font-medium text-stone-700 shadow-sm hover:bg-white transition-colors"
    >
      {isAuthenticated() ? "My LYKKE" : "Log in"}
    </a>
  );

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
    <>
      <SEO
        title="Lykke — Find happiness in everyday moments"
        description="Lykke (loo-kah) — the Danish art of finding happiness in everyday moments. A daily companion for people who struggle with the basics and want calmer, more consistent days."
        path="/"
      />
      <div class="min-h-screen relative overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50" />
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.15)_0%,_transparent_50%)]" />
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.1)_0%,_transparent_50%)]" />

        <AccountLink />

        <div class="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
        <div class="absolute bottom-32 left-10 w-48 h-48 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />
        <div class="absolute top-1/2 left-1/3 w-32 h-32 bg-gradient-to-r from-yellow-200/20 to-orange-200/20 rounded-full blur-2xl" />

        <div class="relative z-10 flex flex-col items-center px-6 py-20 md:py-28">
          <div class="max-w-3xl w-full text-center">
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
                  Lykke
                  <span class="text-stone-400 not-italic text-lg">(n.)</span> —
                  the Danish art of finding happiness in everyday moments.
                </p>
                <p class="text-stone-400 text-sm tracking-wide uppercase">
                  pronounced: loo-kah
                </p>
              </div>
            </div>

            <div
              class="my-16 transition-all duration-1000 delay-[400ms] ease-out"
              style={{
                opacity: mounted() ? 1 : 0,
                transform: mounted() ? "translateY(0)" : "translateY(20px)",
              }}
            >
              <A
                href="/early-access"
                class="group relative inline-flex items-center justify-center px-10 py-4 bg-gradient-to-r from-stone-800 to-stone-700 text-amber-50 rounded-xl hover:from-stone-700 hover:to-stone-600 transition-all duration-300 shadow-lg shadow-stone-900/20 hover:shadow-xl hover:shadow-stone-900/25 hover:-translate-y-0.5"
              >
                <span class="relative z-10 font-medium tracking-wide">
                  Get early access
                </span>
                <div class="absolute inset-0 rounded-xl bg-gradient-to-r from-amber-400/20 to-orange-400/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </A>
            </div>

            <p
              class="text-stone-500 text-base md:text-lg mb-8 max-w-md mx-auto leading-relaxed transition-all duration-1000 delay-300 ease-out"
              style={{
                opacity: mounted() ? 1 : 0,
                transform: mounted() ? "translateY(0)" : "translateY(20px)",
              }}
            >
              A daily companion for adulting — not a productivity app. Lykke is
              for anyone who struggles with the basics. Small intentions, gentle
              check-ins, and just-enough structure.
            </p>

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

            <div
              class="my-20 transition-all duration-1000 delay-[900ms] ease-out"
              style={{
                opacity: mounted() ? 1 : 0,
                transform: mounted() ? "translateY(0)" : "translateY(20px)",
              }}
            >
              <div class="max-w-2xl mx-auto mb-12 text-center">
                <h2 class="text-2xl md:text-3xl font-semibold text-stone-800 mb-6 tracking-tight">
                  What is lykke.day?
                </h2>
                <p class="text-stone-600 text-base md:text-lg leading-relaxed mb-10">
                  A calm, daily system for adulting — built for people who
                  struggle with executive function and need the basics to feel
                  doable. It was created from lived experience of missing the
                  simplest personal tasks.
                </p>
              </div>

              <div class="max-w-5xl mx-auto">
                <div class="grid md:grid-cols-3 gap-6">
                  <div class="bg-white/60 backdrop-blur-sm border border-white/60 rounded-2xl p-6 hover:bg-white/70 transition-all duration-300">
                    <div class="flex flex-col items-center text-center">
                      <div class="flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center mb-4">
                        <Icon path={arrowPath} class="w-7 h-7 text-amber-700" />
                      </div>
                      <div class="flex-1">
                        <h3 class="text-stone-900 font-semibold text-lg mb-3">
                          The comfort of routines
                        </h3>
                        <p class="text-stone-600 text-sm leading-relaxed">
                          There's a quiet confidence that comes from knowing
                          what to do next. Your routines become second nature,
                          freeing your mind for what really matters.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div class="bg-white/60 backdrop-blur-sm border border-white/60 rounded-2xl p-6 hover:bg-white/70 transition-all duration-300">
                    <div class="flex flex-col items-center text-center">
                      <div class="flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center mb-4">
                        <Icon path={heart} class="w-7 h-7 text-amber-700" />
                      </div>
                      <div class="flex-1">
                        <h3 class="text-stone-900 font-semibold text-lg mb-3">
                          The calmness of successful days
                        </h3>
                        <p class="text-stone-600 text-sm leading-relaxed">
                          End your day knowing you showed up. Not perfectly, but
                          meaningfully. That sense of accomplishment creates a
                          peace that compounds over time.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div class="bg-white/60 backdrop-blur-sm border border-white/60 rounded-2xl p-6 hover:bg-white/70 transition-all duration-300">
                    <div class="flex flex-col items-center text-center">
                      <div class="flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center mb-4">
                        <Icon path={sparkles} class="w-7 h-7 text-amber-700" />
                      </div>
                      <div class="flex-1">
                        <h3 class="text-stone-900 font-semibold text-lg mb-3">
                          The freedom to focus on what's big
                        </h3>
                        <p class="text-stone-600 text-sm leading-relaxed">
                          When the small stuff is handled, your energy flows
                          toward your dreams, your relationships, your growth.
                          The things you can't outsource to an app.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div
              class="my-20 transition-all duration-1000 delay-[950ms] ease-out"
              style={{
                opacity: mounted() ? 1 : 0,
                transform: mounted() ? "translateY(0)" : "translateY(20px)",
              }}
            >
              <div class="max-w-2xl mx-auto mb-12 text-center">
                <h2 class="text-2xl md:text-3xl font-semibold text-stone-800 mb-6 tracking-tight">
                  What lykke is not
                </h2>
                <p class="text-stone-600 text-base md:text-lg leading-relaxed mb-10">
                  We're intentionally different. Here's what you won't find
                  here.
                </p>
              </div>

              <div class="max-w-5xl mx-auto">
                <div class="grid md:grid-cols-3 gap-6">
                  <div class="bg-white/60 backdrop-blur-sm border border-white/60 rounded-2xl p-6 hover:bg-white/70 transition-all duration-300">
                    <div class="flex flex-col items-center text-center">
                      <div class="flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-stone-100 to-stone-200 flex items-center justify-center mb-4">
                        <Icon path={xCircle} class="w-7 h-7 text-stone-500" />
                      </div>
                      <div class="flex-1">
                        <h3 class="text-stone-900 font-semibold text-lg mb-3">
                          A Todo List App
                        </h3>
                        <p class="text-stone-600 text-sm leading-relaxed">
                          No endless backlogs or overflowing task lists. Just
                          what matters today.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div class="bg-white/60 backdrop-blur-sm border border-white/60 rounded-2xl p-6 hover:bg-white/70 transition-all duration-300">
                    <div class="flex flex-col items-center text-center">
                      <div class="flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-stone-100 to-stone-200 flex items-center justify-center mb-4">
                        <Icon path={xCircle} class="w-7 h-7 text-stone-500" />
                      </div>
                      <div class="flex-1">
                        <h3 class="text-stone-900 font-semibold text-lg mb-3">
                          A Productivity Tool
                        </h3>
                        <p class="text-stone-600 text-sm leading-relaxed">
                          We're not about doing more. We're about living better
                          — with intention and ease.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div class="bg-white/60 backdrop-blur-sm border border-white/60 rounded-2xl p-6 hover:bg-white/70 transition-all duration-300">
                    <div class="flex flex-col items-center text-center">
                      <div class="flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-stone-100 to-stone-200 flex items-center justify-center mb-4">
                        <Icon path={xCircle} class="w-7 h-7 text-stone-500" />
                      </div>
                      <div class="flex-1">
                        <h3 class="text-stone-900 font-semibold text-lg mb-3">
                          For People With Everything Together
                        </h3>
                        <p class="text-stone-600 text-sm leading-relaxed">
                          If your ducks are already in a row, this probably
                          isn't for you.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div
              class="my-16 transition-all duration-1000 delay-[1000ms] ease-out"
              style={{
                opacity: mounted() ? 1 : 0,
                transform: mounted() ? "translateY(0)" : "translateY(20px)",
              }}
            >
              <h2 class="text-2xl md:text-3xl font-semibold text-stone-800 mb-4 tracking-tight">
                Is Lykke For You?
              </h2>
              <p class="text-stone-600 text-base md:text-lg mb-8 max-w-2xl mx-auto leading-relaxed">
                If you keep missing the basics, forget the small stuff, or feel
                stuck in a loop you can't break, this is for you. Lykke is for
                anyone who struggles with executive function in daily life —
                high achiever or not.
              </p>

              <div class="grid sm:grid-cols-3 gap-4 md:gap-5 mb-6 max-w-3xl mx-auto">
                <div class="bg-white/50 backdrop-blur-sm border border-amber-200/60 rounded-xl p-5 text-center hover:bg-white/70 hover:border-amber-300/70 transition-all duration-300">
                  <div class="text-2xl mb-2">🌱</div>
                  <h4 class="text-stone-800 font-medium text-sm mb-2">
                    Anxiety & Depression
                  </h4>
                  <p class="text-stone-500 text-xs leading-relaxed">
                    Daily structure and gentle routines create stability when
                    everything feels overwhelming.
                  </p>
                </div>

                <div class="bg-white/50 backdrop-blur-sm border border-amber-200/60 rounded-xl p-5 text-center hover:bg-white/70 hover:border-amber-300/70 transition-all duration-300">
                  <div class="text-2xl mb-2">🎯</div>
                  <h4 class="text-stone-800 font-medium text-sm mb-2">
                    ADD & ADHD
                  </h4>
                  <p class="text-stone-500 text-xs leading-relaxed">
                    One day at a time, with reminders that help without adding
                    to the noise.
                  </p>
                </div>

                <div class="bg-white/50 backdrop-blur-sm border border-amber-200/60 rounded-xl p-5 text-center hover:bg-white/70 hover:border-amber-300/70 transition-all duration-300">
                  <div class="text-2xl mb-2">💪</div>
                  <h4 class="text-stone-800 font-medium text-sm mb-2">
                    Substance Abuse Recovery
                  </h4>
                  <p class="text-stone-500 text-xs leading-relaxed">
                    Daily structure and accountability help build the foundation
                    for lasting sobriety — one day at a time.
                  </p>
                </div>
              </div>

              <p class="text-stone-500 text-sm max-w-2xl mx-auto leading-relaxed italic">
                This isn't about having your life perfectly together. It's about
                building gentle, consistent habits so the basics feel possible —
                your way, at your pace.
              </p>
            </div>

            <div class="mt-8 mb-16 space-y-3">
              <div>
                <A
                  href="/resources"
                  class="text-stone-600 text-base md:text-lg underline decoration-amber-400 underline-offset-4 hover:text-stone-800 transition-colors"
                >
                  Not ready? Check out our collection of resources.
                </A>
              </div>
            </div>
          </div>
        </div>

        <div class="relative z-10">
          <Footer />
        </div>
      </div>
    </>
  );
};

export default Landing;
