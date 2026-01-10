import { Component } from "solid-js";
import MediaPage from "@/components/shared/MediaPage";
import { MediaItem } from "@/components/shared/MediaCard";

const weightLossApps: MediaItem[] = [
  {
    title: "MyFitnessPal",
    creator: "MyFitnessPal, Inc.",
    summary:
      "Massive food database with barcode scanning and macro tracking—the reliable workhorse that turns nutrition into numbers.",
    url: "https://www.myfitnesspal.com",
    vibe: "data-driven clarity",
    thumbnail: "/images/weight-loss-apps/myfitnesspal.jpg",
  },
  {
    title: "Noom",
    creator: "Noom, Inc.",
    summary:
      "Psychology-based program with daily lessons, color-coded foods, and personal coaching—rewires habits, not just calories.",
    url: "https://www.noom.com",
    vibe: "mindset shift",
    thumbnail: "/images/weight-loss-apps/noom.jpg",
  },
  {
    title: "Lose It!",
    creator: "FitNow, Inc.",
    summary:
      "Clean calorie counter with snap-it photo logging and community challenges—straightforward tracking without the overwhelm.",
    url: "https://www.loseit.com",
    vibe: "simple momentum",
    thumbnail: "/images/weight-loss-apps/loseit.jpg",
  },
  {
    title: "WeightWatchers",
    creator: "WW International",
    summary:
      "Points system with flexibility for real life, workshops, and decades of proven results—structure that adapts.",
    url: "https://www.weightwatchers.com",
    vibe: "trusted system",
    thumbnail: "/images/weight-loss-apps/weightwatchers.jpg",
  },
  {
    title: "Cronometer",
    creator: "Cronometer Software Inc.",
    summary:
      "Precision nutrition tracking with micronutrients, biometrics, and science-backed data—for detail-oriented optimizers.",
    url: "https://cronometer.com",
    vibe: "deep analytics",
    thumbnail: "/images/weight-loss-apps/cronometer.jpg",
  },
];

const WeightLossApps: Component = () => {
  return (
    <MediaPage
      title="Great Weight Loss Apps"
      subtitle="great weight loss apps"
      description="lykke.day helps you plan the day—these apps help you track the details. Whether you count calories or change habits, sustainable progress comes from consistent attention."
      items={weightLossApps}
      linkText="Visit Site"
    />
  );
};

export default WeightLossApps;

