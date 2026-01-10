import { Component } from "solid-js";
import MediaPage from "@/components/shared/MediaPage";
import { MediaItem } from "@/components/shared/MediaCard";

const channels: MediaItem[] = [
  {
    title: "How to ADHD",
    creator: "Jessica McCabe",
    summary:
      "Evidence-based strategies for managing ADHD with compassion, humor, and community—helping you understand your brain and build systems that actually work.",
    url: "https://www.youtube.com/@HowtoADHD",
    vibe: "adhd support",
    thumbnail: "/images/covers/youtube/how-to-adhd.jpg",
  },
  {
    title: "Therapy in a Nutshell",
    creator: "Emma McAdam, LMFT",
    summary:
      "Accessible mental health education from a licensed therapist—CBT skills, anxiety tools, and practical ways to improve your emotional wellbeing.",
    url: "https://www.youtube.com/@TherapyinaNutshell",
    vibe: "mental health skills",
    thumbnail: "/images/covers/youtube/therapy-in-a-nutshell.jpg",
  },
  {
    title: "HealthyGamerGG",
    creator: "Dr. Alok Kanojia",
    summary:
      "A Harvard-trained psychiatrist blending modern mental health science with ancient yogic wisdom—conversations on gaming, addiction, motivation, and finding purpose.",
    url: "https://www.youtube.com/@HealthyGamerGG",
    vibe: "mental wellness",
    thumbnail: "/images/covers/youtube/healthy-gamer.jpg",
  },
  {
    title: "Ali Abdaal",
    creator: "Ali Abdaal",
    summary:
      "A doctor-turned-creator sharing evidence-based productivity, happiness research, and reflections on building a meaningful life with intention.",
    url: "https://www.youtube.com/@aliabdaal",
    vibe: "productive joy",
    thumbnail: "/images/covers/youtube/ali-abdaal.jpg",
  },
  {
    title: "Matt D'Avella",
    creator: "Matt D'Avella",
    summary:
      "Minimalism, intentional living, and habits—exploring what it means to live with less clutter, more purpose, and deeper presence.",
    url: "https://www.youtube.com/@mattdavella",
    vibe: "intentional living",
    thumbnail: "/images/covers/youtube/matt-d-avella.jpg",
  },
  {
    title: "The School of Life",
    creator: "The School of Life",
    summary:
      "Philosophical guidance on relationships, work, meaning, and self-knowledge—tools for living more wisely and compassionately.",
    url: "https://www.youtube.com/@theschooloflifetv",
    vibe: "wisdom & meaning",
    thumbnail: "/images/covers/youtube/the-school-of-life.jpg",
  },
  {
    title: "Nathaniel Drew",
    creator: "Nathaniel Drew",
    summary:
      "Personal experiments in mindfulness, productivity, and living abroad—reflective storytelling on designing a life aligned with your values.",
    url: "https://www.youtube.com/@NathanielDrew",
    vibe: "mindful exploration",
    thumbnail: "/images/covers/youtube/nathaniel-drew.jpg",
  },
  {
    title: "Elizabeth Filips",
    creator: "Elizabeth Filips",
    summary:
      "A medical student and artist sharing research-backed methods for focus, learning, and managing attention in a distracted world.",
    url: "https://www.youtube.com/@elizabethfilips",
    vibe: "focus & learning",
    thumbnail: "/images/covers/youtube/elizabeth-filips.jpg",
  },
  {
    title: "Sisyphus 55",
    creator: "Sisyphus 55",
    summary:
      "Philosophy through storytelling—existentialism, absurdism, and the search for meaning in everyday life, beautifully narrated.",
    url: "https://www.youtube.com/@Sisyphus55",
    vibe: "existential reflection",
    thumbnail: "/images/covers/youtube/sisyphus-55.jpg",
  },
];

const YouTube: Component = () => {
  return (
    <MediaPage
      title="Lykke.day YouTube Channels"
      subtitle="lykke.day youtube"
      description="Channels that explore attention, rest, purpose, and kinder systems—voices that helped me rethink productivity and presence while building lykke.day."
      items={channels}
    />
  );
};

export default YouTube;
