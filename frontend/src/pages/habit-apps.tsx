import { Component } from "solid-js";
import MediaPage from "@/components/shared/MediaPage";
import { MediaItem } from "@/components/shared/MediaCard";

const habitApps: MediaItem[] = [
  {
    title: "Habitica",
    creator: "HabitRPG, Inc.",
    summary:
      "Gamify your life—turn habits into quests, earn rewards, and level up your avatar as you check off real-world tasks.",
    url: "https://habitica.com",
    vibe: "playful adventure",
    thumbnail: "/images/habit-apps/habitica.jpg",
  },
  {
    title: "Streaks",
    creator: "Crunchy Bagel",
    summary:
      "iOS-exclusive elegance—track up to 12 daily habits with a clean interface that integrates beautifully with Apple Health.",
    url: "https://streaksapp.com",
    vibe: "simple momentum",
    thumbnail: "/images/habit-apps/streaks.jpg",
  },
  {
    title: "Productive",
    creator: "Apalon Apps",
    summary:
      "Smart scheduling for habits—set different times for different days, get motivational stats, and build sustainable routines.",
    url: "https://productiveapp.io",
    vibe: "intelligent routine",
    thumbnail: "/images/habit-apps/productive.jpg",
  },
  {
    title: "Done",
    creator: "Done Labs",
    summary:
      "Flexible habit tracker with custom goals, powerful streaks, and motivational insights—see patterns emerge over time.",
    url: "https://www.done.app",
    vibe: "data-driven progress",
    thumbnail: "/images/habit-apps/done.jpg",
  },
  {
    title: "Loop Habit Tracker",
    creator: "Álinson S Xavier",
    summary:
      "Open-source Android tracker with beautiful graphs, detailed history, and no ads—privacy-focused habit building.",
    url: "https://loophabits.org",
    vibe: "transparent simplicity",
    thumbnail: "/images/habit-apps/loop-habit-tracker.jpg",
  },
  {
    title: "Way of Life",
    creator: "Way of Life ApS",
    summary:
      "Visual chain method—see your progress at a glance with colorful grids, track good and bad habits, spot patterns.",
    url: "https://wayoflifeapp.com",
    vibe: "visual patterns",
    thumbnail: "/images/habit-apps/way-of-life.jpg",
  },
  {
    title: "Strides",
    creator: "Strides Apps LLC",
    summary:
      "Flexible goal tracker—habits, targets, averages, and projects all in one place with customizable tracking methods.",
    url: "https://www.stridesapp.com",
    vibe: "versatile tracking",
    thumbnail: "/images/habit-apps/strides.jpg",
  },
  {
    title: "Fabulous",
    creator: "TheFabulous",
    summary:
      "Science-backed journey builder—guided coaching, mindfulness, and habit stacking that evolves with you over time.",
    url: "https://www.thefabulous.co",
    vibe: "holistic growth",
    thumbnail: "/images/habit-apps/fabulous.jpg",
  },
];

const HabitApps: Component = () => {
  return (
    <MediaPage
      title="Great Habit Apps"
      subtitle="great habit apps"
      description="lykke.day isn't a habit tracker—there are already plenty of excellent ones. These tools excel at building streaks and tracking consistency. We focus on something different: designing days that feel good to live."
      items={habitApps}
      linkText="Visit Site"
    />
  );
};

export default HabitApps;

