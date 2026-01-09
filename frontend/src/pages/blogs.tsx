import { Component } from "solid-js";
import MediaPage from "@/components/shared/MediaPage";
import { MediaItem } from "@/components/shared/MediaCard";

const blogs: MediaItem[] = [
  {
    title: "Nir and Far",
    creator: "Nir Eyal",
    summary:
      "Insights on behavioral design, distraction, and building habits that serve you—practical tools for becoming indistractable in modern life.",
    url: "https://www.nirandfar.com",
    vibe: "attention design",
    thumbnail: "https://www.nirandfar.com/wp-content/uploads/2019/09/nir-eyal-headshot.jpg",
  },
  {
    title: "Zen Habits",
    creator: "Leo Babauta",
    summary:
      "Minimalist reflections on simplifying life, forming habits, and finding calm in the chaos—wisdom from two decades of mindful practice.",
    url: "https://zenhabits.net",
    vibe: "simple living",
    thumbnail: "https://zenhabits.net/wp-content/uploads/2021/01/leo-babauta-zen-habits.jpg",
  },
  {
    title: "Mark Manson",
    creator: "Mark Manson",
    summary:
      "No-nonsense essays on living with intention, accepting reality, and choosing what matters—refreshingly honest takes on modern life.",
    url: "https://markmanson.net",
    vibe: "honest clarity",
    thumbnail: "https://markmanson.net/wp-content/uploads/2019/03/mark-manson-headshot.jpg",
  },
  {
    title: "Wait But Why",
    creator: "Tim Urban",
    summary:
      "Deep dives into procrastination, decision-making, and life's big questions with stick figures and humor—making complex ideas wonderfully accessible.",
    url: "https://waitbutwhy.com",
    vibe: "curious exploration",
    thumbnail: "https://waitbutwhy.com/wp-content/uploads/2015/05/tim-urban.jpg",
  },
  {
    title: "The Art of Manliness",
    creator: "Brett McKay",
    summary:
      "Timeless advice on character, resilience, and practical skills for living well—rooted in history, focused on becoming your best self.",
    url: "https://www.artofmanliness.com",
    vibe: "grounded wisdom",
    thumbnail: "https://content.artofmanliness.com/uploads/2019/01/brett-mckay.jpg",
  },
  {
    title: "Brain Pickings (The Marginalian)",
    creator: "Maria Popova",
    summary:
      "Literary connections across art, science, and philosophy—curated reflections on what makes life meaningful and beautiful.",
    url: "https://www.themarginalian.org",
    vibe: "wonder & connection",
    thumbnail: "https://www.themarginalian.org/wp-content/uploads/2019/01/maria-popova.jpg",
  },
  {
    title: "Cal Newport's Blog",
    creator: "Cal Newport",
    summary:
      "Research and strategies for deep work, digital minimalism, and building a focused life—practical philosophy for knowledge workers.",
    url: "https://calnewport.com/blog",
    vibe: "deep focus",
    thumbnail: "https://calnewport.com/wp-content/uploads/2019/03/cal-newport-headshot.jpg",
  },
  {
    title: "Barking Up The Wrong Tree",
    creator: "Eric Barker",
    summary:
      "Science-backed insights on success, happiness, and relationships—entertaining research summaries that challenge conventional wisdom.",
    url: "https://www.bakadesuyo.com",
    vibe: "research & wit",
    thumbnail: "https://www.bakadesuyo.com/wp-content/uploads/2019/01/eric-barker.jpg",
  },
  {
    title: "ADHD Alien",
    creator: "Pina Varnel",
    summary:
      "Illustrated comics capturing ADHD experiences with warmth and humor—visual explanations that help you feel seen and understood.",
    url: "https://adhd-alien.com",
    vibe: "adhd comfort",
    thumbnail: "https://adhd-alien.com/wp-content/uploads/2020/01/adhd-alien-profile.jpg",
  },
  {
    title: "Raptitude",
    creator: "David Cain",
    summary:
      "Thoughtful experiments in mindfulness, minimalism, and getting better at being human—reflective essays on living deliberately.",
    url: "https://www.raptitude.com",
    vibe: "mindful living",
    thumbnail: "https://www.raptitude.com/wp-content/uploads/2019/01/david-cain.jpg",
  },
  {
    title: "Becoming Minimalist",
    creator: "Joshua Becker",
    summary:
      "Practical guidance on decluttering, simplifying, and finding freedom in owning less—encouraging stories from the minimalism movement.",
    url: "https://www.becomingminimalist.com",
    vibe: "intentional space",
    thumbnail: "https://www.becomingminimalist.com/wp-content/uploads/2019/01/joshua-becker.jpg",
  },
  {
    title: "Study Hacks",
    creator: "Cal Newport",
    summary:
      "Academic and career advice focused on deliberate practice, focus, and building remarkable skills without burning out.",
    url: "https://www.calnewport.com/blog",
    vibe: "strategic learning",
    thumbnail: "https://calnewport.com/wp-content/uploads/2019/03/cal-newport-headshot.jpg",
  },
];

const Blogs: Component = () => {
  return (
    <MediaPage
      title="Lykke.day Blogs & Websites"
      subtitle="lykke.day blogs"
      description="Writers and thinkers exploring attention, purpose, and intentional living—voices that shaped my path toward rest and reflection while creating lykke.day."
      items={blogs}
      linkText="Visit"
    />
  );
};

export default Blogs;

