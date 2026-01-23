import { Component, createMemo } from "solid-js";
import { useNavigate } from "@solidjs/router";
import Page from "@/components/shared/layout/Page";
import { Quote } from "@/components/shared/Quote";
import { Icon } from "@/components/shared/Icon";
import { faArrowLeft } from "@fortawesome/free-solid-svg-icons";
import { setShowTodayCookie } from "@/utils/cookies";

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

export const ThatsAllPage: Component = () => {
  const navigate = useNavigate();

  // Pick a quote (based on day of year for consistency)
  const selectedQuote = createMemo(() => {
    const today = new Date();
    const dayOfYear = Math.floor(
      (today.getTime() - new Date(today.getFullYear(), 0, 0).getTime()) /
        (1000 * 60 * 60 * 24)
    );
    return endOfDayQuotes[dayOfYear % endOfDayQuotes.length];
  });

  return (
    <Page>
      <div class="max-w-2xl mx-auto px-6 py-12 min-h-[70vh] flex flex-col justify-center">
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-amber-100 to-orange-100 mb-6 shadow-lg">
            <span class="text-4xl">🌙</span>
          </div>
          <h2 class="text-2xl md:text-3xl font-semibold text-stone-800 mb-3">
            That's all she wrote...
          </h2>
        </div>

        <div class="mb-8">
          <Quote
            quote={selectedQuote().quote}
            author={selectedQuote().author}
            quoteClass="text-stone-600 text-lg md:text-xl italic leading-relaxed px-6 text-center"
          />
        </div>

        <div class="text-center">
          <p class="text-stone-700 text-xl md:text-2xl font-medium">
            Rest well. Tomorrow is a new day.
          </p>
        </div>

        <div class="mt-6 flex justify-center">
          <button
            type="button"
            onClick={() => {
              setShowTodayCookie();
              navigate("/me");
            }}
            class="inline-flex items-center gap-2 text-stone-600 hover:text-stone-800 transition-colors"
            aria-label="Back to home"
          >
            <Icon icon={faArrowLeft} class="w-4 h-4" />
            <span class="text-sm">I changed my mind, I've got more to do</span>
          </button>
        </div>
      </div>
    </Page>
  );
};

export default ThatsAllPage;
