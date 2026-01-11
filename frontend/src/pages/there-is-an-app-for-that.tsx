import { Component, For, createSignal, onMount } from "solid-js";
import { A } from "@solidjs/router";
import { Icon } from "solid-heroicons";
import {
  devicePhoneMobile,
  sparkles,
  chartBar,
  heart,
  checkCircle,
  faceFrown,
  fire,
} from "solid-heroicons/outline";
import Footer from "@/components/shared/layout/Footer";

interface AppCategory {
  icon: typeof devicePhoneMobile;
  title: string;
  subtitle: string;
  link: string;
  satireText: string;
}

const ThereIsAnAppForThat: Component = () => {
  const [mounted, setMounted] = createSignal(false);

  onMount(() => {
    setTimeout(() => setMounted(true), 50);
  });

  const categories: AppCategory[] = [
    {
      icon: checkCircle,
      title: "Todo Apps",
      subtitle: "For forgetting what you're supposed to do",
      link: "/apps/todo",
      satireText:
        "37 apps later, you're still not sure which one holds the grocery list from Tuesday.",
    },
    {
      icon: sparkles,
      title: "Meditation Apps",
      subtitle: "For stressing about whether you're relaxing correctly",
      link: "/apps/meditation",
      satireText:
        "Nothing says 'inner peace' like comparing your streak to strangers and gamifying mindfulness.",
    },
    {
      icon: chartBar,
      title: "Weight Loss Apps",
      subtitle: "For turning food into a math problem",
      link: "/apps/weight-loss",
      satireText:
        "Because eating intuitively is no match for scanning barcodes and judging your lunch in real-time.",
    },
    {
      icon: fire,
      title: "Habit Apps",
      subtitle: "For gamifying basic human functioning",
      link: "/apps/habits",
      satireText:
        "Lose your 847-day streak and watch your sense of self-worth crumble. At least you flossed consistently for two years though.",
    },
    {
      icon: heart,
      title: "Happiness Apps",
      subtitle: "For quantifying joy until it becomes homework",
      link: "/apps/happiness",
      satireText:
        "Daily gratitude prompts and mood tracking—because being happy is so much easier when you journal about it at 11 PM.",
    },
  ];

  const otherResources = [
    { title: "Books", link: "/books", emoji: "📚" },
    { title: "Podcasts", link: "/podcasts", emoji: "🎧" },
    { title: "YouTube Channels", link: "/youtube", emoji: "📺" },
  ];

  return (
    <div class="min-h-screen relative overflow-hidden">
      {/* Background */}
      <div class="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.15)_0%,_transparent_50%)]" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.1)_0%,_transparent_50%)]" />

      {/* Floating orbs */}
      <div class="absolute top-20 right-10 w-64 h-64 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
      <div class="absolute bottom-32 left-10 w-48 h-48 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />

      <div class="relative z-10 flex flex-col items-center px-6 py-20 md:py-28">
        <div class="max-w-2xl w-full">
          {/* Header */}
          <div
            class="text-center mb-16 transition-all duration-1000 ease-out"
            style={{
              opacity: mounted() ? 1 : 0,
              transform: mounted() ? "translateY(0)" : "translateY(-20px)",
            }}
          >
            <div class="flex justify-center mb-6">
              <div class="relative">
                <Icon
                  path={devicePhoneMobile}
                  class="w-16 h-16 text-amber-600"
                />
                <Icon
                  path={sparkles}
                  class="w-6 h-6 text-rose-500 absolute -top-2 -right-2 animate-pulse"
                />
              </div>
            </div>

            <h1 class="text-4xl md:text-6xl font-bold tracking-tight text-stone-800 mb-6">
              There's an App for That
              <span class="text-amber-500">.</span>
            </h1>

            <div class="max-w-2xl mx-auto space-y-6">
              <p class="text-stone-600 text-lg md:text-xl leading-relaxed">
                Can't sleep? There's an app. Can't focus? There's an app. Can't
                remember which app you downloaded to help you remember things?
                There's an app for that too.
              </p>

              <div class="bg-white/60 backdrop-blur-md border border-white/80 rounded-2xl px-8 py-6">
                <p
                  class="text-stone-700 text-xl md:text-2xl italic leading-relaxed"
                  style={{
                    "font-family": "'Cormorant Garamond', Georgia, serif",
                  }}
                >
                  In 2025, we've optimized, gamified, and subscribed our way to
                  peak… confusion.
                </p>
              </div>

              <p class="text-stone-600 text-base md:text-lg leading-relaxed">
                But seriously—some of these apps are genuinely helpful. We've
                curated lists of the good ones. Because even though we're being
                cheeky, we know tools matter. Just maybe not 47 of them.
              </p>
            </div>
          </div>

          {/* App Categories */}
          <div
            class="grid md:grid-cols-1 lg:grid-cols-2 gap-6 mb-12 transition-all duration-1000 delay-200 ease-out"
            style={{
              opacity: mounted() ? 1 : 0,
              transform: mounted() ? "translateY(0)" : "translateY(30px)",
            }}
          >
            <For each={categories}>
              {(category, index) => (
                <a
                  href={category.link}
                  class="group bg-white/50 backdrop-blur-sm border border-white/60 rounded-2xl p-8 text-center hover:bg-white/70 hover:shadow-xl hover:shadow-amber-900/10 transition-all duration-300 hover:-translate-y-1"
                  style={{
                    opacity: mounted() ? 1 : 0,
                    transform: mounted() ? "translateY(0)" : "translateY(30px)",
                    transition: `all 0.8s ease-out ${0.3 + index() * 0.1}s`,
                  }}
                >
                  <div class="flex justify-center mb-4">
                    <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center group-hover:from-amber-200 group-hover:to-orange-200 transition-colors duration-300">
                      <Icon
                        path={category.icon}
                        class="w-7 h-7 text-amber-700"
                      />
                    </div>
                  </div>

                  <h3 class="text-stone-800 font-semibold text-xl mb-2">
                    {category.title}
                  </h3>

                  <p class="text-stone-500 text-sm mb-4 italic">
                    {category.subtitle}
                  </p>

                  <p class="text-stone-600 text-sm leading-relaxed">
                    {category.satireText}
                  </p>

                  <div class="mt-6 text-amber-600 font-medium text-sm group-hover:text-amber-700 transition-colors">
                    View the list →
                  </div>
                </a>
              )}
            </For>
          </div>

          {/* Combined Reality Check & Resources Section */}
          <div
            class="max-w-4xl mx-auto mb-12 transition-all duration-1000 delay-500 ease-out"
            style={{
              opacity: mounted() ? 1 : 0,
              transform: mounted() ? "translateY(0)" : "translateY(20px)",
            }}
          >
            <div class="bg-white/60 backdrop-blur-md border border-white/80 rounded-3xl shadow-xl shadow-stone-900/5 overflow-hidden">
              {/* Top section - The Irony */}
              <div class="bg-gradient-to-br from-stone-50 to-amber-50/50 px-8 py-10 text-center">
                <div class="flex justify-center mb-4">
                  <Icon path={faceFrown} class="w-10 h-10 text-rose-500" />
                </div>
                <h3 class="text-stone-900 font-bold text-2xl mb-4">
                  The Irony Isn't Lost On Us
                </h3>
                <p class="text-stone-700 text-base leading-relaxed mb-3">
                  Yes, lykke.day is also an app. But instead of asking you to
                  track 47 metrics across 12 dashboards, we're trying something
                  radical:{" "}
                  <span class="font-semibold text-stone-900">
                    one simple question each day
                  </span>
                  .
                </p>
                <p class="text-stone-600 text-lg italic font-serif">
                  "What would make today feel good?"
                </p>
              </div>

              {/* Bottom section - Not Everything Needs an App */}
              <div class="px-8 py-10">
                <h3 class="text-stone-900 font-bold text-2xl mb-6 text-center">
                  Some non app-based resources :)
                </h3>

                <div class="grid sm:grid-cols-3 gap-5 mb-6">
                  <For each={otherResources}>
                    {(resource) => (
                      <a
                        href={resource.link}
                        class="group relative bg-gradient-to-br from-stone-50 to-white border border-stone-200 rounded-2xl p-6 text-center hover:border-amber-300 hover:shadow-lg hover:shadow-amber-900/10 transition-all duration-300 hover:-translate-y-1"
                      >
                        <div class="text-5xl mb-3 group-hover:scale-110 transition-transform duration-300">
                          {resource.emoji}
                        </div>
                        <h4 class="text-stone-800 font-semibold text-base group-hover:text-stone-900 transition-colors">
                          {resource.title}
                        </h4>
                        <div class="absolute inset-0 rounded-2xl bg-gradient-to-br from-amber-100/0 to-orange-100/0 group-hover:from-amber-100/20 group-hover:to-orange-100/20 transition-all duration-300 pointer-events-none" />
                      </a>
                    )}
                  </For>
                </div>
              </div>
            </div>
          </div>

          {/* Footer CTA */}
          <div
            class="text-center mt-16 transition-all duration-1000 delay-700 ease-out"
            style={{
              opacity: mounted() ? 1 : 0,
              transform: mounted() ? "translateY(0)" : "translateY(20px)",
            }}
          >
            <A
              href="/early-access"
              class="inline-flex items-center justify-center px-8 py-3 bg-gradient-to-r from-stone-800 to-stone-700 text-amber-50 rounded-xl hover:from-stone-700 hover:to-stone-600 transition-all duration-300 shadow-lg shadow-stone-900/20 hover:shadow-xl hover:-translate-y-0.5"
            >
              <span class="font-medium">Try lykke.day instead</span>
            </A>
          </div>
        </div>
      </div>

      <div class="relative z-10">
        <Footer />
      </div>
    </div>
  );
};

export default ThereIsAnAppForThat;
