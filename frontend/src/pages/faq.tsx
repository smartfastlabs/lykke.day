import { Component, For } from "solid-js";
import { Icon } from "solid-heroicons";
import { chatBubbleLeftRight, heart, sparkles } from "solid-heroicons/outline";
import Footer from "@/components/shared/layout/Footer";

interface FAQItem {
  question: string;
  answer: string;
  icon: typeof chatBubbleLeftRight;
}

const faqs: FAQItem[] = [
  {
    question: "What is lykke?",
    answer:
      "Lykke (loo-kah) is a Danish idea of everyday happiness. We're borrowing that spirit to design gentle routines, kind prompts, and calm space for what matters — not hustle.",
    icon: sparkles,
  },
  {
    question: "Is this another Todo App?",
    answer:
      "Nope. lykke.day is a daily companion built to ease pressure, not pile on tasks. We focus on one gentle day at a time, mindful routines, and soft check-ins instead of endless backlogs.",
    icon: sparkles,
  },
  {
    question: "Why lykke.day?",
    answer:
      "Because most tools add weight. We remove friction: one clear day view, routines that flex, and reminders that nudge not nag. It's built to feel like a caring friend, not a boss.",
    icon: heart,
  },
  {
    question: "Who is this for?",
    answer:
      "People in a season of change: feeling low or stuck, easing back from burnout, working through recovery (alcohol, drugs, loss), or navigating a midlife reset. If you want gentle structure, kind nudges, and space to heal at your own pace, lykke.day is for you.",
    icon: heart,
  },
  {
    question: "I'm too busy — I don't have time to do MORE?",
    answer:
      "We designed for exactly that. Plan once in a few minutes, get soft reminders, and check in with a couple taps. No backlog guilt, just a light daily rhythm that fits into real life.",
    icon: chatBubbleLeftRight,
  },
  {
    question: "How much does it cost?",
    answer:
      "During early access, it's free. We'll introduce a simple paid plan when we're confident it delivers daily value — with a generous trial and clear communication before anything changes.",
    icon: chatBubbleLeftRight,
  },
];

const FAQ: Component = () => {
  return (
    <div class="min-h-screen relative overflow-hidden bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 flex flex-col">
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.12)_0%,_transparent_45%)]" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.12)_0%,_transparent_45%)]" />
      <div class="absolute top-24 right-16 w-56 h-56 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
      <div class="absolute bottom-24 left-12 w-44 h-44 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />

      <div class="relative z-10 max-w-3xl mx-auto px-6 py-16 flex-1 w-full">
        <div class="bg-white/70 backdrop-blur-md border border-white/70 rounded-3xl shadow-xl shadow-amber-900/5 p-8 md:p-10">
          <h1 class="text-3xl md:text-4xl font-bold text-stone-800 mb-6">
            lykke.day FAQs:
          </h1>
          <p class="text-stone-600 text-base md:text-lg leading-relaxed mb-10">
            We're building a calm, day-at-a-time companion. Here are quick
            answers to what most people ask before they join.
          </p>

          <div class="space-y-4">
            <For each={faqs}>
              {(item) => (
                <div class="group bg-white/80 border border-white/80 rounded-2xl p-6 hover:shadow-lg hover:shadow-amber-900/8 transition-all duration-300">
                  <div class="flex items-start gap-4">
                    <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center group-hover:from-amber-200 group-hover:to-orange-200 transition-colors duration-300">
                      <Icon path={item.icon} class="w-6 h-6 text-amber-700" />
                    </div>
                    <div class="space-y-2">
                      <h2 class="text-lg font-semibold text-stone-800">
                        {item.question}
                      </h2>
                      <p class="text-stone-600 leading-relaxed">
                        {item.answer}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </For>
          </div>

          <div class="mt-10 bg-gradient-to-br from-stone-800 to-stone-700 rounded-2xl p-7 md:p-8 text-amber-50 shadow-lg shadow-stone-900/15 border border-white/10">
            <div class="flex flex-col md:flex-row md:items-center gap-5 md:gap-8">
              <div class="space-y-2 flex-1">
                <p class="text-xs uppercase tracking-[0.25em] text-amber-200/80">
                  early access
                </p>
                <p class="text-2xl font-semibold">
                  Ready for a gentler day? Join the waitlist.
                </p>
                <p class="text-amber-50/80 text-sm md:text-base leading-relaxed">
                  Get first access to lykke.day, gentle reminders, and calm
                  routines built for busy, changing seasons.
                </p>
              </div>
              <a
                href="/early-access"
                class="group relative inline-flex items-center justify-center px-8 py-3 bg-amber-100 text-stone-900 rounded-xl font-medium tracking-wide hover:bg-amber-200 transition-all duration-300 shadow-md shadow-stone-900/20 hover:-translate-y-0.5"
              >
                <span class="relative z-10">Get early access</span>
                <div class="absolute inset-0 rounded-xl bg-amber-400/30 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </a>
            </div>
          </div>

          <div class="mt-6 text-center">
            <a
              href="/there-is-an-app-for-that"
              class="text-stone-500 text-sm underline decoration-rose-300 underline-offset-4 hover:text-stone-700 transition-colors"
            >
              Looking for other apps &amp; resources? Check our guide →
            </a>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default FAQ;
