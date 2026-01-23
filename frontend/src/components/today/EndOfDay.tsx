import { Component, createMemo } from "solid-js";
import { MotivationalQuote } from "@/components/shared/MotivationalQuote";

// Array of positive quotes for end of day
const endOfDayQuotes = [
  {
    quote: "You showed up today. That's enough. Rest well.",
    author: "lykke",
  },
  {
    quote: "The day is done. You've done what you could. Tomorrow is a fresh start.",
    author: "lykke",
  },
  {
    quote: "Rest is not a reward for finishing everything. Rest is a requirement for living well.",
    author: "lykke",
  },
  {
    quote: "You've completed another day. Take a moment to appreciate that.",
    author: "lykke",
  },
  {
    quote: "The best way to take care of tomorrow is to rest well tonight.",
    author: "lykke",
  },
];

export const EndOfDay: Component = () => {
  // Pick a random quote (based on day of year for consistency)
  const selectedQuote = createMemo(() => {
    const today = new Date();
    const dayOfYear = Math.floor(
      (today.getTime() - new Date(today.getFullYear(), 0, 0).getTime()) /
        (1000 * 60 * 60 * 24)
    );
    return endOfDayQuotes[dayOfYear % endOfDayQuotes.length];
  });

  return (
    <div class="max-w-2xl mx-auto py-12 px-6">
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 mb-6 shadow-lg">
          <span class="text-4xl">🌙</span>
        </div>
        <h2 class="text-2xl md:text-3xl font-semibold text-stone-800 mb-3">
          End of Day
        </h2>
        <p class="text-stone-600 text-base md:text-lg">
          You've completed all your tasks and reminders for today.
        </p>
      </div>

      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-8 md:p-12 backdrop-blur-sm">
        <MotivationalQuote
          quote={selectedQuote().quote}
          author={selectedQuote().author}
        />
      </div>

      <div class="text-center mt-8">
        <p class="text-stone-500 text-sm md:text-base">
          Rest well. Tomorrow is a new day.
        </p>
      </div>
    </div>
  );
};
