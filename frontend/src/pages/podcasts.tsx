import { Component } from "solid-js";
import MediaPage from "@/components/shared/MediaPage";
import { MediaItem } from "@/components/shared/MediaCard";

const podcasts: MediaItem[] = [
  {
    title: "Huberman Lab",
    creator: "Dr. Andrew Huberman",
    summary:
      "Neuroscience professor breaking down sleep, focus, dopamine, and stress with actionable protocols for optimizing your brain and body.",
    url: "https://www.hubermanlab.com/",
    vibe: "science & protocols",
    thumbnail: "/images/covers/podcasts/huberman-lab.webp",
  },
  {
    title: "The Happiness Lab",
    creator: "Dr. Laurie Santos",
    summary:
      "Yale psychologist unpacking the science of happiness—why our instincts mislead us and what actually brings lasting wellbeing.",
    url: "https://www.pushkin.fm/podcasts/the-happiness-lab-with-dr-laurie-santos",
    vibe: "wellbeing science",
    thumbnail: "/images/covers/podcasts/the-happiness-lab.webp",
  },
  {
    title: "Ten Percent Happier",
    creator: "Dan Harris",
    summary:
      "Meditation for skeptics—conversations with mindfulness teachers, therapists, and scientists on building a calmer, less reactive life.",
    url: "https://www.danharris.com/s/10-happier",
    vibe: "practical meditation",
    thumbnail: "/images/covers/podcasts/10-percent-happier.webp",
  },
  {
    title: "Hidden Brain",
    creator: "Shankar Vedantam",
    summary:
      "Stories and research on the unconscious patterns that drive our decisions, relationships, and sense of self—illuminating the invisible forces shaping daily life.",
    url: "https://hiddenbrain.org/",
    vibe: "behavioral science",
    thumbnail: "/images/covers/podcasts/hidden-brain.webp",
  },
  {
    title: "The ADHD Experts Podcast",
    creator: "ADDitude Magazine",
    summary:
      "Clinicians, coaches, and adults with ADHD sharing strategies for executive function, emotional regulation, and building systems that stick.",
    url: "https://additudemag.libsyn.com/",
    vibe: "adhd strategies",
    thumbnail: "/images/covers/podcasts/adhd-experts.png",
  },
  {
    title: "On Being",
    creator: "Krista Tippett",
    summary:
      "Intimate conversations with poets, theologians, and thinkers on meaning, resilience, and what it means to be human—spacious, contemplative, and deeply grounding.",
    url: "https://onbeing.org/series/podcast/",
    vibe: "meaning & contemplation",
    thumbnail: "/images/covers/podcasts/on-being.webp",
  },
  {
    title: "Feel Better, Live More",
    creator: "Dr. Rangan Chatterjee",
    summary:
      "A UK doctor interviewing experts on stress, sleep, movement, and nutrition—small changes for a healthier, more balanced life.",
    url: "https://drchatterjee.com/podcast/",
    vibe: "holistic health",
    thumbnail: "/images/covers/podcasts/feel-better-live-more.png",
  },
  {
    title: "Terrible, Thanks for Asking",
    creator: "Nora McInerny",
    summary:
      "Honest, funny, heartbreaking conversations about grief, hardship, and the messy parts of being human—permission to not be okay.",
    url: "https://feelingsand.co/podcasts/terrible-thanks-for-asking/",
    vibe: "honest emotions",
    thumbnail: "/images/covers/podcasts/terrible-thanks-for-asking.webp",
  },
  {
    title: "We Can Do Hard Things",
    creator: "Glennon Doyle",
    summary:
      "Author Glennon Doyle and her family navigating relationships, identity, and courage—warm, vulnerable conversations on becoming who you are.",
    url: "https://momastery.com/podcast/",
    vibe: "brave living",
    thumbnail: "/images/covers/podcasts/we-can-do-hard-things.webp",
  },
  {
    title: "The Tim Ferriss Show",
    creator: "Tim Ferriss",
    summary:
      "Deep dives with world-class performers on their routines, failures, and systems—deconstructing excellence across every field.",
    url: "https://tim.blog/podcast/",
    vibe: "performance & systems",
    thumbnail: "/images/covers/podcasts/tim-ferris.webp",
  },
];

const Podcasts: Component = () => {
  return (
    <MediaPage
      title="Lykke.day Podcasts"
      subtitle="lykke.day podcasts"
      description="Podcasts on attention, burnout recovery, and building a kinder relationship with productivity—voices that shaped my thinking while creating lykke.day."
      items={podcasts}
    />
  );
};

export default Podcasts;
