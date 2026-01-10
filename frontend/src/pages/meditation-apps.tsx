import { Component } from "solid-js";
import MediaPage from "@/components/shared/MediaPage";
import { MediaItem } from "@/components/shared/MediaCard";

const meditationApps: MediaItem[] = [
  {
    title: "Headspace",
    creator: "Headspace Inc.",
    summary:
      "Friendly guided meditation with animated explainers, sleep sounds, and mindful movement—meditation made approachable and fun.",
    url: "https://www.headspace.com",
    vibe: "playful calm",
    thumbnail: "/images/meditation-apps/headspace.jpg",
  },
  {
    title: "Calm",
    creator: "Calm.com",
    summary:
      "Soothing library of meditations, sleep stories, and nature scenes—Matthew McConaughey's voice will tuck you in.",
    url: "https://www.calm.com",
    vibe: "peaceful sanctuary",
    thumbnail: "/images/meditation-apps/calm.jpg",
  },
  {
    title: "Insight Timer",
    creator: "Insight Network Inc.",
    summary:
      "Massive free library with 100k+ meditations from teachers worldwide—courses, music, and community without subscription walls.",
    url: "https://insighttimer.com",
    vibe: "generous abundance",
    thumbnail: "/images/meditation-apps/insight-timer.jpg",
  },
  {
    title: "Ten Percent Happier",
    creator: "Ten Percent Happier",
    summary:
      "Practical meditation for skeptics with down-to-earth teachers, video lessons, and a no-BS approach to mindfulness.",
    url: "https://www.tenpercent.com",
    vibe: "real & grounded",
    thumbnail: "/images/meditation-apps/ten-percent.jpg",
  },
  {
    title: "Waking Up",
    creator: "Sam Harris",
    summary:
      "Secular meditation course diving deep into consciousness and the nature of mind—philosophy meets practice.",
    url: "https://www.wakingup.com",
    vibe: "intellectual depth",
    thumbnail: "/images/meditation-apps/waking-up.jpg",
  },
  {
    title: "Balance",
    creator: "Elevate Labs",
    summary:
      "Personalized meditation plans that adapt daily to your mood and goals—fresh content that evolves with you.",
    url: "https://www.balanceapp.com",
    vibe: "adaptive growth",
    thumbnail: "/images/meditation-apps/balance.jpg",
  },
  {
    title: "Oak",
    creator: "Oak Meditation & Breathing",
    summary:
      "Simple, free meditation with no ads, no subscriptions, just breathing exercises and unguided sessions—clean focus.",
    url: "https://www.oakmeditation.com",
    vibe: "minimalist zen",
    thumbnail: "/images/meditation-apps/oak.jpg",
  },
  {
    title: "Simple Habit",
    creator: "Simple Habit Inc.",
    summary:
      "5-minute meditations for busy schedules with sessions for specific situations—commuting, stress, sleep, focus.",
    url: "https://www.simplehabit.com",
    vibe: "quick relief",
    thumbnail: "/images/meditation-apps/simple-habit.jpg",
  },
];

const MeditationApps: Component = () => {
  return (
    <MediaPage
      title="Great Meditation Apps"
      subtitle="great meditation apps"
      description="lykke.day helps you plan time for stillness—these apps guide you through it. Whether you're curious or committed, there's a teacher and style waiting for you."
      items={meditationApps}
      linkText="Visit Site"
    />
  );
};

export default MeditationApps;

