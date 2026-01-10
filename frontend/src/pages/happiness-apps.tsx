import { Component } from "solid-js";
import MediaPage from "@/components/shared/MediaPage";
import { MediaItem } from "@/components/shared/MediaCard";

const happinessApps: MediaItem[] = [
  {
    title: "Happify",
    creator: "Happify, Inc.",
    summary:
      "Science-based activities and games designed to reduce stress and build resilience—positive psychology turned into playful daily practices.",
    url: "https://www.happify.com",
    vibe: "joyful science",
    thumbnail: "/images/happiness-apps/happify.jpg",
  },
  {
    title: "SuperBetter",
    creator: "SuperBetter Labs",
    summary:
      "Gamified resilience builder that turns life challenges into quests—level up your mental strength with allies, power-ups, and bad guys to defeat.",
    url: "https://www.superbetter.com",
    vibe: "heroic growth",
    thumbnail: "/images/happiness-apps/superbetter.jpg",
  },
  {
    title: "Gratitude",
    creator: "Hapjoy Technologies",
    summary:
      "Beautiful gratitude journal with daily prompts, photos, and reflection—capture moments that matter and watch patterns of joy emerge.",
    url: "https://www.gratitudeapp.com",
    vibe: "mindful appreciation",
    thumbnail: "/images/happiness-apps/gratitude.jpg",
  },
  {
    title: "Jour",
    creator: "Jour App",
    summary:
      "Guided gratitude journal with thoughtful prompts and mood tracking—build the habit of noticing good with gentle daily nudges.",
    url: "https://jour.app",
    vibe: "gentle reflection",
    thumbnail: "/images/happiness-apps/jour.jpg",
  },
  {
    title: "Shine",
    creator: "Shine",
    summary:
      "Daily self-care texts and audio support for mental wellness—like a caring friend checking in with encouragement and practical tools.",
    url: "https://www.theshineapp.com",
    vibe: "warm support",
    thumbnail: "/images/happiness-apps/shine.jpg",
  },
  {
    title: "Reflectly",
    creator: "Reflectly ApS",
    summary:
      "AI-powered journal that learns from your entries and asks smart questions—track moods, spot patterns, and understand yourself better.",
    url: "https://reflectly.app",
    vibe: "intelligent insight",
    thumbnail: "/images/happiness-apps/reflectly.jpg",
  },
  {
    title: "Day One",
    creator: "Automattic",
    summary:
      "Premium journaling app with rich media, templates, and encryption—capture life's moments beautifully across all your devices.",
    url: "https://dayoneapp.com",
    vibe: "thoughtful chronicle",
    thumbnail: "/images/happiness-apps/day-one.jpg",
  },
  {
    title: "Presently",
    creator: "Presently",
    summary:
      "Simple gratitude journal with no frills—one prompt per day, private entries, and a growing archive of what made you smile.",
    url: "https://presently.app",
    vibe: "pure simplicity",
    thumbnail: "/images/happiness-apps/presently.jpg",
  },
];

const HappinessApps: Component = () => {
  return (
    <MediaPage
      title="Great Happiness Apps"
      subtitle="great happiness apps"
      description="lykke.day helps you design days that feel good—these apps help you notice, track, and amplify the good that's already there. Small daily practices that shift your baseline joy."
      items={happinessApps}
      linkText="Visit Site"
    />
  );
};

export default HappinessApps;

