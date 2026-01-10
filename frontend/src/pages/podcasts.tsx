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
    thumbnail: "https://megaphone.imgix.net/podcasts/1d2a3364-8f67-11eb-a52e-5fe051f8cb9e/image/8a6da51677c34fc3cb77acf36d6ca9f3.jpeg",
  },
  {
    title: "The Happiness Lab",
    creator: "Dr. Laurie Santos",
    summary:
      "Yale psychologist unpacking the science of happiness—why our instincts mislead us and what actually brings lasting wellbeing.",
    url: "https://www.pushkin.fm/podcasts/the-happiness-lab-with-dr-laurie-santos",
    vibe: "wellbeing science",
    thumbnail: "https://www.omnycontent.com/d/programs/4b5f9d6d-7fdf-4c4e-95af-ac46003721e9/ab1af4c0-9608-439b-9dc0-ac46003721e9/image.jpg",
  },
  {
    title: "Maintenance Phase",
    creator: "Michael Hobbes & Aubrey Gordon",
    summary:
      "Debunking wellness fads and diet culture myths with research, humor, and compassion—a kinder lens on health and body culture.",
    url: "https://www.maintenancephase.com/",
    vibe: "wellness myths",
    thumbnail: "https://megaphone.imgix.net/podcasts/8a9d4d4c-cda4-11ea-9d28-3b5567b520a4/image/8a9d4d4c-cda4-11ea-9d28-3b5567b520a4_image.jpeg",
  },
  {
    title: "Ten Percent Happier",
    creator: "Dan Harris",
    summary:
      "Meditation for skeptics—conversations with mindfulness teachers, therapists, and scientists on building a calmer, less reactive life.",
    url: "https://www.tenpercent.com/podcast",
    vibe: "practical meditation",
    thumbnail: "https://megaphone.imgix.net/podcasts/f8f6ea94-7f30-11e7-837f-5326313b3be1/image/uploads_2F1501181536034-nnk5ndfp8t-a7fbb2a96b1e2f9d3be43ae03a7c9379_2FTen_Percent_Happier_With_Dan_Harris_3000x3000.jpg",
  },
  {
    title: "Hidden Brain",
    creator: "Shankar Vedantam",
    summary:
      "Stories and research on the unconscious patterns that drive our decisions, relationships, and sense of self—illuminating the invisible forces shaping daily life.",
    url: "https://hiddenbrain.org/",
    vibe: "behavioral science",
    thumbnail: "https://media.npr.org/assets/img/2018/01/17/hidden-brain-logo-tile_sq-49b3f93d6e49a5aff9f12ae0804d1fcdb0f83c79.jpg",
  },
  {
    title: "The ADHD Experts Podcast",
    creator: "ADDitude Magazine",
    summary:
      "Clinicians, coaches, and adults with ADHD sharing strategies for executive function, emotional regulation, and building systems that stick.",
    url: "https://www.additudemag.com/category/webinar/audio-replay/",
    vibe: "adhd strategies",
    thumbnail: "https://www.additudemag.com/wp-content/uploads/2020/06/ADDitude-ADHD-Experts-Podcast-1400x1400-1.png",
  },
  {
    title: "On Being",
    creator: "Krista Tippett",
    summary:
      "Intimate conversations with poets, theologians, and thinkers on meaning, resilience, and what it means to be human—spacious, contemplative, and deeply grounding.",
    url: "https://onbeing.org/series/podcast/",
    vibe: "meaning & contemplation",
    thumbnail: "https://cdn.onbeing.org/wp-content/uploads/2023/09/19095628/OnBeing_PodcastCover_3000x3000_2023.jpg",
  },
  {
    title: "Feel Better, Live More",
    creator: "Dr. Rangan Chatterjee",
    summary:
      "A UK doctor interviewing experts on stress, sleep, movement, and nutrition—small changes for a healthier, more balanced life.",
    url: "https://drchatterjee.com/podcast/",
    vibe: "holistic health",
    thumbnail: "https://drchatterjee.com/wp-content/uploads/2023/02/Dr-Chatterjee-Podcast-Covers.jpg",
  },
  {
    title: "Terrible, Thanks for Asking",
    creator: "Nora McInerny",
    summary:
      "Honest, funny, heartbreaking conversations about grief, hardship, and the messy parts of being human—permission to not be okay.",
    url: "https://www.apmpodcasts.org/ttfa/",
    vibe: "honest emotions",
    thumbnail: "https://www.apmpodcasts.org/ttfa/wp-content/uploads/sites/8/2023/05/TTFA-3000x3000-1.png",
  },
  {
    title: "We Can Do Hard Things",
    creator: "Glennon Doyle",
    summary:
      "Author Glennon Doyle and her family navigating relationships, identity, and courage—warm, vulnerable conversations on becoming who you are.",
    url: "https://momastery.com/podcast/",
    vibe: "brave living",
    thumbnail: "https://megaphone.imgix.net/podcasts/cca26f06-ea5c-11ea-8c95-2f4cbf11e6f4/image/We_Can_Do_Hard_Things_Cover_Art.png",
  },
  {
    title: "The Ground Up Show",
    creator: "Matt D'Avella",
    summary:
      "Interviews with creators, entrepreneurs, and minimalists on building intentional lives—habits, work, and what matters most.",
    url: "https://mattdavella.com/podcast",
    vibe: "intentional creators",
    thumbnail: "https://images.squarespace-cdn.com/content/v1/58d20c79725e25b221549193/1596731645062-BVJG9P9M2QKT97YT5TP1/TheGroundUp.jpg",
  },
  {
    title: "The Tim Ferriss Show",
    creator: "Tim Ferriss",
    summary:
      "Deep dives with world-class performers on their routines, failures, and systems—deconstructing excellence across every field.",
    url: "https://tim.blog/podcast/",
    vibe: "performance & systems",
    thumbnail: "https://megaphone.imgix.net/podcasts/6cd0c1d8-f17f-11eb-8016-9f5d3fa88b26/image/uploads_2F1547576425296-fmtxnluk8a-b44be1c5e9196b6cb1cc8a2cd15e6cd0_2F2019_Podcast_artwork_1440x1440.jpg",
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

