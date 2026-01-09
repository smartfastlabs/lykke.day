import { Component, For } from "solid-js";
import Footer from "@/components/shared/layout/Footer";

interface Book {
  title: string;
  author: string;
  summary: string;
  isbn: string;
  amazonUrl: string;
  vibe?: string;
  cover?: string;
}

const books: Book[] = [
  {
    title: "Dopamine Nation",
    author: "Anna Lembke, MD",
    summary:
      "A look at why modern life overstimulates our reward systems and how to reset with intentional abstinence, balance, and honest self-inventory.",
    isbn: "9781524746739",
    amazonUrl: "https://www.amazon.com/dp/1524746730",
    vibe: "craving & balance",
    cover: "/covers/dopamine-nation.jpg",
  },
  {
    title: "Build the Life You Want",
    author: "Arthur C. Brooks & Oprah Winfrey",
    summary:
      "Practical habits from positive psychology—agency, connection, and meaning—to design a steadier, happier daily rhythm.",
    isbn: "9780593545400",
    amazonUrl: "https://www.amazon.com/dp/0593545400",
    vibe: "design your days",
    cover: "/covers/build-the-life-you-want.jpg",
  },
  {
    title: "The Alchemist",
    author: "Paulo Coelho",
    summary:
      "A gentle parable about listening to your heart, following small omens, and trusting the slow path to your own personal legend.",
    isbn: "9780061122415",
    amazonUrl: "https://www.amazon.com/dp/0061122416",
    vibe: "hopeful fiction",
    cover: "/covers/the-alchemist.jpg",
  },
  {
    title: "The Little Book of Hygge",
    author: "Meik Wiking",
    summary:
      "Simple rituals—candles, cozy corners, shared meals—that turn ordinary days into warm, calm moments of hygge.",
    isbn: "9780062658807",
    amazonUrl: "https://www.amazon.com/dp/0062658808",
    vibe: "cozy living",
    cover: "/covers/the-little-book-of-hygge.jpg",
  },
  {
    title: "The Little Book of Lykke",
    author: "Meik Wiking",
    summary:
      "Stories and research on why certain communities feel happier, with small practices that travel well into daily life.",
    isbn: "9780062820334",
    amazonUrl: "https://www.amazon.com/dp/0062820338",
    vibe: "everyday joy",
    cover: "/covers/the-little-book-of-lykke.jpg",
  },
  {
    title: "Four Thousand Weeks",
    author: "Oliver Burkeman",
    summary:
      "A calming reset on time: accept limits, choose what matters, and let go of the productivity race.",
    isbn: "9780374159125",
    amazonUrl: "https://www.amazon.com/dp/0374159122",
    vibe: "time sanity",
    cover: "/covers/four-thousand-weeks.jpg",
  },
  {
    title: "Wintering",
    author: "Katherine May",
    summary:
      "A lyrical reminder that hard seasons are natural; we can rest, gather light, and reemerge with new strength.",
    isbn: "9780525535857",
    amazonUrl: "https://www.amazon.com/dp/0525535856",
    vibe: "gentle rest",
    cover: "/covers/wintering.jpg",
  },
  {
    title: "Set Boundaries, Find Peace",
    author: "Nedra Glover Tawwab",
    summary:
      "Clear scripts and practices for saying no, reclaiming energy, and protecting relationships with healthy limits.",
    isbn: "9780593192092",
    amazonUrl: "https://www.amazon.com/dp/0593192095",
    vibe: "calm boundaries",
    cover: "/covers/set-boundaries-find-peace.jpg",
  },
  {
    title: "How to Do Nothing",
    author: "Jenny Odell",
    summary:
      "A reflection on attention as a scarce resource and how to step outside constant consumption to notice the real world again.",
    isbn: "9781612197494",
    amazonUrl: "https://www.amazon.com/dp/1612197493",
    vibe: "attention & presence",
    cover: "/covers/how-to-do-nothing.jpg",
  },
  {
    title: "Driven to Distraction",
    author: "Edward M. Hallowell & John J. Ratey",
    summary:
      "Classic ADHD guide on spotting patterns, reducing overwhelm, and building kinder systems for attention.",
    isbn: "9780307743152",
    amazonUrl: "https://www.amazon.com/dp/0307743152",
    vibe: "attention support",
    cover: "/covers/driven-to-distraction.jpg",
  },
  {
    title: "The Happiness Trap",
    author: "Russ Harris",
    summary:
      "Acceptance and Commitment Therapy guide for getting unstuck from the pursuit of constant happiness and building a values-led life.",
    isbn: "9781590305843",
    amazonUrl:
      "https://www.amazon.com/Happiness-Trap-Struggling-Start-Living/dp/1590305841",
    vibe: "mindful resilience",
  },
  {
    title: "Focused Forward",
    author: "James M. Ochoa",
    summary:
      "Tools for adult ADHD to ride out emotional storms, calm shame spirals, and build steadier routines with compassion.",
    isbn: "9781626342400",
    amazonUrl:
      "https://www.amazon.com/Focused-Forward-Navigating-Storms-Adult/dp/1626342407",
    vibe: "adhd grounding",
  },
  {
    title: "Ikigai: The Japanese Secret to a Long and Happy Life",
    author: "Héctor García & Francesc Miralles",
    summary:
      "A light guide to finding your everyday purpose (ikigai) with small habits, social ties, and mindful movement for a calmer, longer life.",
    isbn: "9780143130727",
    amazonUrl: "https://www.amazon.com/dp/0143130722",
    vibe: "purpose & longevity",
  },
  {
    title: "The Four-Way Path",
    author:
      "The Four-Way Path: A Guide to Purushartha and India's Spiritual Traditions for a Life of Happiness, Success, and Purpose",
    summary:
      "A guide to purushartha—dharma, artha, kama, and moksha—applying India’s four aims of life to modern purpose, prosperity, love, and liberation.",
    isbn: "9781637588896",
    amazonUrl: "https://www.amazon.com/dp/1637588895",
    vibe: "purpose & dharma",
  },
  {
    title: "The Mountain Is You",
    author: "Brianna Wiest",
    summary:
      "On breaking self-sabotage loops by understanding emotional needs, healing patterns, and choosing self-led action.",
    isbn: "9781949759228",
    amazonUrl:
      "https://www.amazon.com/dp/1949759229/ref=sspa_dk_detail_2?psc=1&pd_rd_i=1949759229&pd_rd_w=H9a35&content-id=amzn1.sym.8c2f9165-8e93-42a1-8313-73d3809141a2&pf_rd_p=8c2f9165-8e93-42a1-8313-73d3809141a2&pf_rd_r=5JCYSYT637EMTTDEZQ1A&pd_rd_wg=8aaxx&pd_rd_r=e9308a97-d2f6-4c38-bb3d-b2ab188e5b64&sp_csd=d2lkZ2V0TmFtZT1zcF9kZXRhaWw",
    vibe: "self-mastery",
  },
];

const coverUrl = (isbn: string) =>
  `https://covers.openlibrary.org/b/isbn/${isbn}-L.jpg`;
const fallbackCover = "https://placehold.co/240x320?text=No+Cover";
const resolveCover = (book: Book) => book.cover ?? coverUrl(book.isbn);

const Books: Component = () => {
  return (
    <div class="min-h-screen relative overflow-hidden bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 flex flex-col">
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.12)_0%,_transparent_45%)]" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.12)_0%,_transparent_45%)]" />
      <div class="absolute top-24 right-16 w-56 h-56 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
      <div class="absolute bottom-24 left-12 w-44 h-44 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />

      <div class="relative z-10 max-w-3xl mx-auto px-6 py-16 flex-1 w-full">
        <a
          href="/"
          class="inline-block mb-8 text-stone-500 hover:text-stone-700 transition-colors text-sm"
        >
          ← Back
        </a>

        <div class="bg-white/70 backdrop-blur-md border border-white/70 rounded-3xl shadow-xl shadow-amber-900/5 p-8 md:p-10">
          <div class="space-y-3">
            <p class="text-xs uppercase tracking-[0.25em] text-amber-400">
              lykke.day bookshelf
            </p>
            <h1 class="text-3xl md:text-4xl font-bold text-stone-800">
              Lykke.day Bookshelf
            </h1>
            <p class="text-stone-600 text-base md:text-lg leading-relaxed max-w-3xl">
              Books I leaned on while recovering from burnout and
              COVID—reflections, routines, and kinder ways to rebuild—that
              nudged me toward creating lykke.day.
            </p>
          </div>

          <div class="mt-8 grid gap-5 sm:grid-cols-2">
            <For each={books}>
              {(book) => (
                <div class="group bg-white border border-amber-100/60 rounded-2xl p-5 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 flex flex-col gap-4">
                  <div class="flex flex-col gap-4">
                    <div class="relative w-full h-56 overflow-hidden rounded-xl shadow-sm shadow-stone-900/10 bg-amber-50">
                      <img
                        src={resolveCover(book)}
                        alt={`${book.title} cover`}
                        class="w-full h-full object-cover"
                        loading="lazy"
                        onError={(event) => {
                          event.currentTarget.onerror = null;
                          event.currentTarget.src = fallbackCover;
                        }}
                      />
                      <div class="absolute inset-0 bg-gradient-to-t from-stone-900/10 to-transparent" />
                    </div>
                    <div class="space-y-2">
                      {book.vibe && (
                        <p class="inline-flex items-center px-2 py-1 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800">
                          {book.vibe}
                        </p>
                      )}
                      <h2 class="text-lg font-semibold text-stone-800 leading-snug">
                        {book.title}
                      </h2>
                      <p class="text-sm text-stone-500">{book.author}</p>
                      <p class="text-sm text-stone-600 leading-relaxed">
                        {book.summary}
                      </p>
                    </div>
                  </div>
                  <div class="flex items-center justify-end text-sm text-stone-500">
                    <a
                      href={book.amazonUrl}
                      target="_blank"
                      rel="noreferrer"
                      class="text-amber-700 hover:text-amber-800 underline underline-offset-4 font-semibold"
                    >
                      Amazon
                    </a>
                  </div>
                </div>
              )}
            </For>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default Books;
