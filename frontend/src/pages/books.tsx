import { Component } from "solid-js";
import MediaPage from "@/components/shared/MediaPage";
import { MediaItem } from "@/components/shared/MediaCard";

const books: MediaItem[] = [
  {
    title: "Dopamine Nation",
    creator: "Anna Lembke, MD",
    summary:
      "A look at why modern life overstimulates our reward systems and how to reset with intentional abstinence, balance, and honest self-inventory.",
    url: "https://www.amazon.com/Dopamine-Nation-Finding-Balance-Indulgence/dp/B08LQZCGDJ",
    vibe: "craving & balance",
    thumbnail: "/images/covers/books/dopamine-nation.jpg",
  },
  {
    title: "Build the Life You Want",
    creator: "Arthur C. Brooks & Oprah Winfrey",
    summary:
      "Practical habits from positive psychology—agency, connection, and meaning—to design a steadier, happier daily rhythm.",
    url: "https://www.amazon.com/dp/0593545400",
    vibe: "design your days",
    thumbnail: "/images/covers/books/build-the-life-you-want.jpg",
  },
  {
    title: "The Little Book of Hygge",
    creator: "Meik Wiking",
    summary:
      "Simple rituals—candles, cozy corners, shared meals—that turn ordinary days into warm, calm moments of hygge.",
    url: "https://www.amazon.com/dp/0062658808",
    vibe: "cozy living",
    thumbnail: "/images/covers/books/the-little-book-of-hygge.jpg",
  },
  {
    title: "The Little Book of Lykke",
    creator: "Meik Wiking",
    summary:
      "Stories and research on why certain communities feel happier, with small practices that travel well into daily life.",
    url: "https://www.amazon.com/dp/0062820338",
    vibe: "everyday joy",
    thumbnail: "/images/covers/books/the-little-book-of-lykke.jpg",
  },
  {
    title: "Four Thousand Weeks",
    creator: "Oliver Burkeman",
    summary:
      "A calming reset on time: accept limits, choose what matters, and let go of the productivity race.",
    url: "https://www.amazon.com/dp/0374159122",
    vibe: "time sanity",
    thumbnail: "/images/covers/books/four-thousand-weeks.jpg",
  },
  {
    title: "Wintering",
    creator: "Katherine May",
    summary:
      "A lyrical reminder that hard seasons are natural; we can rest, gather light, and reemerge with new strength.",
    url: "https://www.amazon.com/Wintering-Power-Retreat-Difficult-Times/dp/B085S72KVX",
    vibe: "gentle rest",
    thumbnail: "/images/covers/books/wintering.jpg",
  },
  {
    title: "Set Boundaries, Find Peace",
    creator: "Nedra Glover Tawwab",
    summary:
      "Clear scripts and practices for saying no, reclaiming energy, and protecting relationships with healthy limits.",
    url: "https://www.amazon.com/dp/0593192095",
    vibe: "calm boundaries",
    thumbnail: "/images/covers/books/set-boundaries-find-peace.jpg",
  },
  {
    title: "How to Do Nothing",
    creator: "Jenny Odell",
    summary:
      "A reflection on attention as a scarce resource and how to step outside constant consumption to notice the real world again.",
    url: "https://www.amazon.com/dp/1612197493",
    vibe: "attention & presence",
    thumbnail: "/images/covers/books/how-to-do-nothing.jpg",
  },
  {
    title: "Driven to Distraction",
    creator: "Edward M. Hallowell & John J. Ratey",
    summary:
      "Classic ADHD guide on spotting patterns, reducing overwhelm, and building kinder systems for attention.",
    url: "https://www.amazon.com/dp/0307743152",
    vibe: "attention support",
    thumbnail: "/images/covers/books/driven-to-distraction.jpg",
  },
  {
    title: "The Happiness Trap",
    creator: "Russ Harris",
    summary:
      "Acceptance and Commitment Therapy guide for getting unstuck from the pursuit of constant happiness and building a values-led life.",
    url: "https://www.amazon.com/Happiness-Trap-Struggling-Start-Living/dp/1590305841",
    vibe: "mindful resilience",
    thumbnail: "/images/covers/books/the-happiness-trap.jpg",
  },
  {
    title: "Focused Forward",
    creator: "James M. Ochoa",
    summary:
      "Tools for adult ADHD to ride out emotional storms, calm shame spirals, and build steadier routines with compassion.",
    url: "https://www.amazon.com/Focused-Forward-Navigating-Storms-Adult/dp/0996983902",
    vibe: "adhd grounding",
    thumbnail: "/images/covers/books/focused-forward.jpg",
  },
  {
    title: "Ikigai: The Japanese Secret to a Long and Happy Life",
    creator: "Héctor García & Francesc Miralles",
    summary:
      "A light guide to finding your everyday purpose (ikigai) with small habits, social ties, and mindful movement for a calmer, longer life.",
    url: "https://www.amazon.com/dp/0143130722",
    vibe: "purpose & longevity",
    thumbnail: "/images/covers/books/ikigai.jpg",
  },
];

const Books: Component = () => {
  return (
    <MediaPage
      title="Lykke.day Bookshelf"
      subtitle="lykke.day bookshelf"
      description="These books resonated with me during my journey to adapting to life after covid—but they're just a starting point.<br><br>There's something powerful about physically reading (yes, turning actual pages, not just listening at 2x speed while doing dishes). Books let you pause mid-sentence, sit with an idea. That depth is hard to replicate.<br><br>All the knowledge in the world won't change your life—it's what you do with your days. These are simply invitations to think differently about how you want to live yours."
      items={books}
    />
  );
};

export default Books;
