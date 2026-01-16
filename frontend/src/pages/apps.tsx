import { Component, For } from "solid-js";
import Footer from "@/components/shared/layout/Footer";
import MediaCard, { MediaItem } from "@/components/shared/MediaCard";
import SEO from "@/components/shared/SEO";

interface AppItem extends MediaItem {}

const apps: AppItem[] = [
  {
    title: "Notion",
    creator: "Notion Labs",
    summary:
      "All-in-one workspace blending notes, databases, tasks, and wikis—flexible building blocks that grow with how you think and work.",
    url: "https://www.notion.so",
    vibe: "flexible & powerful",
    thumbnail: "/images/covers/apps/notion.png",
  },
  {
    title: "Todoist",
    creator: "Doist",
    summary:
      "Clean, fast task manager with natural language input, priorities, and filters—turns messy to-dos into calm clarity.",
    url: "https://todoist.com",
    vibe: "streamlined focus",
    thumbnail: "/images/covers/apps/todoist.png",
  },
  {
    title: "Things 3",
    creator: "Cultured Code",
    summary:
      "Beautifully minimal GTD app for Apple devices—projects, areas, and today view make tasks feel light and approachable.",
    url: "https://culturedcode.com/things/",
    vibe: "elegant simplicity",
    thumbnail: "/images/covers/apps/things.png",
  },
  {
    title: "Asana",
    creator: "Asana, Inc.",
    summary:
      "Team project hub with task dependencies, timelines, and multiple views—scales from solo lists to complex workflows.",
    url: "https://asana.com",
    vibe: "team clarity",
    thumbnail: "/images/covers/apps/asana.png",
  },
  {
    title: "Trello",
    creator: "Atlassian",
    summary:
      "Visual boards and cards for kanban-style planning—drag-and-drop simplicity that makes projects feel organized and alive.",
    url: "https://trello.com",
    vibe: "visual flow",
    thumbnail: "/images/covers/apps/trello.png",
  },
  {
    title: "TickTick",
    creator: "Appest Inc.",
    summary:
      "Feature-packed task manager with calendars, habits, timers, and custom views—all the tools without the clutter.",
    url: "https://ticktick.com",
    vibe: "complete toolkit",
    thumbnail: "/images/covers/apps/ticktick.png",
  },
  {
    title: "Any.do",
    creator: "Any.do",
    summary:
      "Task list meets calendar with voice entry, shared lists, and a gentle daily planning ritual—friendly momentum.",
    url: "https://www.any.do",
    vibe: "daily rhythm",
    thumbnail: "/images/covers/apps/anydo.png",
  },
  {
    title: "Microsoft To Do",
    creator: "Microsoft",
    summary:
      "Simple daily planner with My Day focus, intelligent suggestions, and seamless Office integration—free and reliable.",
    url: "https://todo.microsoft.com",
    vibe: "daily essentials",
    thumbnail: "/images/covers/apps/microsoft-todo.png",
  },
  {
    title: "Headspace",
    creator: "Headspace Inc.",
    summary:
      "Friendly guided meditation with animated explainers, sleep sounds, and mindful movement—meditation made approachable and fun.",
    url: "https://www.headspace.com",
    vibe: "playful calm",
    thumbnail: "/images/covers/apps/headspace.png",
  },
  {
    title: "Calm",
    creator: "Calm.com",
    summary:
      "Soothing library of meditations, sleep stories, and nature scenes—Matthew McConaughey's voice will tuck you in.",
    url: "https://www.calm.com",
    vibe: "peaceful sanctuary",
    thumbnail: "/images/covers/apps/calm.png",
  },
  {
    title: "Insight Timer",
    creator: "Insight Network Inc.",
    summary:
      "Massive free library with 100k+ meditations from teachers worldwide—courses, music, and community without subscription walls.",
    url: "https://insighttimer.com",
    vibe: "generous abundance",
    thumbnail: "/images/covers/apps/insight-timer.png",
  },
  {
    title: "Ten Percent Happier",
    creator: "Ten Percent Happier",
    summary:
      "Practical meditation for skeptics with down-to-earth teachers, video lessons, and a no-BS approach to mindfulness.",
    url: "https://www.tenpercent.com",
    vibe: "real & grounded",
    thumbnail: "/images/covers/apps/ten-percent.png",
  },
  {
    title: "Waking Up",
    creator: "Sam Harris",
    summary:
      "Secular meditation course diving deep into consciousness and the nature of mind—philosophy meets practice.",
    url: "https://www.wakingup.com",
    vibe: "intellectual depth",
    thumbnail: "/images/covers/apps/waking-up.png",
  },
  {
    title: "Day One",
    creator: "Automattic",
    summary:
      "Premium journaling app with rich media, templates, and encryption—capture life's moments beautifully across all your devices.",
    url: "https://dayoneapp.com",
    vibe: "thoughtful chronicle",
    thumbnail: "/images/covers/apps/day-one.png",
  },
  {
    title: "Happify",
    creator: "Happify, Inc.",
    summary:
      "Science-based activities and games designed to reduce stress and build resilience—positive psychology turned into playful daily practices.",
    url: "https://www.happify.com",
    vibe: "joyful science",
    thumbnail: "/images/covers/apps/happify.png",
  },
  {
    title: "SuperBetter",
    creator: "SuperBetter Labs",
    summary:
      "Gamified resilience builder that turns life challenges into quests—level up your mental strength with allies, power-ups, and bad guys to defeat.",
    url: "https://www.superbetter.com",
    vibe: "heroic growth",
    thumbnail: "/images/covers/apps/superbetter.png",
  },
  {
    title: "MyFitnessPal",
    creator: "MyFitnessPal, Inc.",
    summary:
      "Massive food database with barcode scanning and macro tracking—the reliable workhorse that turns nutrition into numbers.",
    url: "https://www.myfitnesspal.com",
    vibe: "data-driven clarity",
    thumbnail: "/images/covers/apps/myfitnesspal.png",
  },
  {
    title: "Noom",
    creator: "Noom, Inc.",
    summary:
      "Psychology-based program with daily lessons, color-coded foods, and personal coaching—rewires habits, not just calories.",
    url: "https://www.noom.com",
    vibe: "mindset shift",
    thumbnail: "/images/covers/apps/noom.png",
  },
  {
    title: "Lose It!",
    creator: "FitNow, Inc.",
    summary:
      "Clean calorie counter with snap-it photo logging and community challenges—straightforward tracking without the overwhelm.",
    url: "https://www.loseit.com",
    vibe: "simple momentum",
    thumbnail: "/images/covers/apps/loseit.png",
  },
  {
    title: "Habitica",
    creator: "HabitRPG, Inc.",
    summary:
      "Gamify your life—turn habits into quests, earn rewards, and level up your avatar as you check off real-world tasks.",
    url: "https://habitica.com",
    vibe: "playful adventure",
    thumbnail: "/images/covers/apps/habitica.png",
  },
  {
    title: "Streaks",
    creator: "Crunchy Bagel",
    summary:
      "iOS-exclusive elegance—track up to 12 daily habits with a clean interface that integrates beautifully with Apple Health.",
    url: "https://streaksapp.com",
    vibe: "simple momentum",
    thumbnail: "/images/covers/apps/streaks.png",
  },
  {
    title: "Strava",
    creator: "Strava, Inc.",
    summary:
      "Social fitness network for runners and cyclists—track workouts, compete on segments, and connect with a global community of athletes.",
    url: "https://www.strava.com",
    vibe: "competitive community",
    thumbnail: "/images/covers/apps/strava.png",
  },
  {
    title: "Fitbit",
    creator: "Fitbit by Google",
    summary:
      "Comprehensive health tracking with activity, sleep, heart rate, and stress monitoring—whole-person wellness in one ecosystem.",
    url: "https://www.fitbit.com",
    vibe: "holistic tracking",
    thumbnail: "/images/covers/apps/fitbit.png",
  },
  {
    title: "Fabulous",
    creator: "TheFabulous",
    summary:
      "Science-backed journey builder—guided coaching, mindfulness, and habit stacking that evolves with you over time.",
    url: "https://www.thefabulous.co",
    vibe: "holistic growth",
    thumbnail: "/images/covers/apps/fabulous.png",
  },
];

const Apps: Component = () => {
  return (
    <>
      <SEO
        title="Apps We've Tried"
        description="From productivity apps and habit trackers to wellness apps, meditation apps, and mental health apps—there are many excellent health and wellness tools available."
        path="/apps"
      />
      <div class="min-h-screen relative overflow-hidden bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 flex flex-col">
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.12)_0%,_transparent_45%)]" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.12)_0%,_transparent_45%)]" />
      <div class="absolute top-24 right-16 w-56 h-56 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
      <div class="absolute bottom-24 left-12 w-44 h-44 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />

      <div class="relative z-10 max-w-4xl mx-auto px-6 py-16 flex-1 w-full">
        <div class="bg-white/70 backdrop-blur-md border border-white/70 rounded-3xl shadow-xl shadow-amber-900/5 p-8 md:p-10">
          <div class="space-y-3">
            <p class="text-xs uppercase tracking-[0.25em] text-amber-400">
              great apps
            </p>
            <h1 class="text-3xl md:text-4xl font-bold text-stone-800">
              Apps We've Tried
            </h1>
            <div class="text-stone-600 text-base md:text-lg leading-relaxed space-y-4">
              <p>
                From productivity apps and habit trackers to wellness apps,
                meditation apps, and mental health apps—there are many excellent
                health and wellness tools available. I've tried quite a few of
                them.
              </p>
              <p>
                While these wellness apps and productivity tools can be helpful,
                they work best when you have a clear foundation of what matters
                to you and why. Health apps and mindfulness apps are most
                effective when you have intention and clarity about your goals.
              </p>
              <p>
                That's where lykke comes in—a foundation that helps you
                establish clarity and intention, making your wellness apps and
                other tools more effective.
              </p>
            </div>
          </div>

          <div class="mt-8 grid gap-5 sm:grid-cols-2">
            <For each={apps}>
              {(app) => <MediaCard item={app} />}
            </For>
          </div>
        </div>
      </div>

      <Footer />
    </div>
    </>
  );
};

export default Apps;
