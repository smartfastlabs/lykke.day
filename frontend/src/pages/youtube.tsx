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
    thumbnail: "https://yt3.googleusercontent.com/ytc/AIdro_miWXKhDxGO8y8QhLa9jVx9u4bPqKTMz4m7A7v4Dw=s176-c-k-c0x00ffffff-no-rj",
  },
  {
    title: "Therapy in a Nutshell",
    creator: "Emma McAdam, LMFT",
    summary:
      "Accessible mental health education from a licensed therapist—CBT skills, anxiety tools, and practical ways to improve your emotional wellbeing.",
    url: "https://www.youtube.com/@TherapyinaNutshell",
    vibe: "mental health skills",
    thumbnail: "https://yt3.googleusercontent.com/4g6d8W2QoPsI-tqmvKdEb5nfXPQPUPQZp6_1gW8g75kqJVs7iVL_3CW0eP-SqKW4U_4BXZyP=s176-c-k-c0x00ffffff-no-rj",
  },
  {
    title: "HealthyGamerGG",
    creator: "Dr. Alok Kanojia",
    summary:
      "A Harvard-trained psychiatrist blending modern mental health science with ancient yogic wisdom—conversations on gaming, addiction, motivation, and finding purpose.",
    url: "https://www.youtube.com/@HealthyGamerGG",
    vibe: "mental wellness",
    thumbnail: "https://yt3.googleusercontent.com/ytc/AIdro_kGP3t5pG5L6_8R8fJ8o3P1w_7Q5lYa_6kD3yWRdw=s176-c-k-c0x00ffffff-no-rj",
  },
  {
    title: "CGP Grey",
    creator: "CGP Grey",
    summary:
      "Deeply researched explanations of systems, productivity philosophy, and how to think about life's complex questions with clarity and curiosity.",
    url: "https://www.youtube.com/@CGPGrey",
    vibe: "systems thinking",
    thumbnail: "https://yt3.googleusercontent.com/ytc/AIdro_kL-2P7xJXdJCVGpSLp6XYVpC3b7-3bQp6M3Q=s176-c-k-c0x00ffffff-no-rj",
  },
  {
    title: "Kurzgesagt – In a Nutshell",
    creator: "Kurzgesagt Team",
    summary:
      "Beautifully animated explorations of science, philosophy, and existential topics—making the universe's biggest questions accessible and wondrous.",
    url: "https://www.youtube.com/@kurzgesagt",
    vibe: "wonder & science",
    thumbnail: "https://yt3.googleusercontent.com/ytc/AIdro_n5BHq3z7Fvqy86FPxPzZ5h5BdGlI9YdW-7yTpQ=s176-c-k-c0x00ffffff-no-rj",
  },
  {
    title: "Ali Abdaal",
    creator: "Ali Abdaal",
    summary:
      "A doctor-turned-creator sharing evidence-based productivity, happiness research, and reflections on building a meaningful life with intention.",
    url: "https://www.youtube.com/@aliabdaal",
    vibe: "productive joy",
    thumbnail: "https://yt3.googleusercontent.com/ytc/AIdro_lxrFBPELZDrq97VBUcQCZ8h6BdPBvv5vBqow=s176-c-k-c0x00ffffff-no-rj",
  },
  {
    title: "Matt D'Avella",
    creator: "Matt D'Avella",
    summary:
      "Minimalism, intentional living, and habits—exploring what it means to live with less clutter, more purpose, and deeper presence.",
    url: "https://www.youtube.com/@mattdavella",
    vibe: "intentional living",
    thumbnail: "https://yt3.googleusercontent.com/ytc/AIdro_mmkUPBT4KfnhJ0pRXb4k2Hn_5qP_6zLw=s176-c-k-c0x00ffffff-no-rj",
  },
  {
    title: "Struthless",
    creator: "Campbell Walker",
    summary:
      "Creative systems, productivity for messy brains, and honest reflections on building a life that works when your attention wanders.",
    url: "https://www.youtube.com/@Struthless",
    vibe: "creative systems",
    thumbnail: "https://yt3.googleusercontent.com/ytc/AIdro_nQhVv9HjYPX3h7TQrZBLfqR6PZ5xaX-9M=s176-c-k-c0x00ffffff-no-rj",
  },
  {
    title: "The School of Life",
    creator: "The School of Life",
    summary:
      "Philosophical guidance on relationships, work, meaning, and self-knowledge—tools for living more wisely and compassionately.",
    url: "https://www.youtube.com/@theschooloflifetv",
    vibe: "wisdom & meaning",
    thumbnail: "https://yt3.googleusercontent.com/ytc/AIdro_l5PqMw8f3H6Y3Z9rH7L8Ej0BvLqQ=s176-c-k-c0x00ffffff-no-rj",
  },
  {
    title: "Nathaniel Drew",
    creator: "Nathaniel Drew",
    summary:
      "Personal experiments in mindfulness, productivity, and living abroad—reflective storytelling on designing a life aligned with your values.",
    url: "https://www.youtube.com/@NathanielDrew",
    vibe: "mindful exploration",
    thumbnail: "https://yt3.googleusercontent.com/ytc/AIdro_lW8Q5L6ZM8x7h9R5qX3Pw=s176-c-k-c0x00ffffff-no-rj",
  },
  {
    title: "Elizabeth Filips",
    creator: "Elizabeth Filips",
    summary:
      "A medical student and artist sharing research-backed methods for focus, learning, and managing attention in a distracted world.",
    url: "https://www.youtube.com/@elizabethfilips",
    vibe: "focus & learning",
    thumbnail: "https://yt3.googleusercontent.com/ytc/AIdro_kZ5Y3P7H-qL9w8xB6R5pQ=s176-c-k-c0x00ffffff-no-rj",
  },
  {
    title: "Sisyphus 55",
    creator: "Sisyphus 55",
    summary:
      "Philosophy through storytelling—existentialism, absurdism, and the search for meaning in everyday life, beautifully narrated.",
    url: "https://www.youtube.com/@Sisyphus55",
    vibe: "existential reflection",
    thumbnail: "https://yt3.googleusercontent.com/ytc/AIdro_mK7Z5qH8R-9LwX6pM=s176-c-k-c0x00ffffff-no-rj",
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

