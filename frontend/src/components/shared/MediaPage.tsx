import { Component, For } from "solid-js";
import Footer from "@/components/shared/layout/Footer";
import MediaCard, { MediaItem } from "@/components/shared/MediaCard";

interface MediaPageProps {
  title: string;
  subtitle: string;
  description: string;
  items: MediaItem[];
}

const MediaPage: Component<MediaPageProps> = (props) => {
  return (
    <div class="min-h-screen relative overflow-hidden bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 flex flex-col">
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(251,191,36,0.12)_0%,_transparent_45%)]" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(244,114,82,0.12)_0%,_transparent_45%)]" />
      <div class="absolute top-24 right-16 w-56 h-56 bg-gradient-to-br from-amber-200/30 to-orange-200/20 rounded-full blur-3xl" />
      <div class="absolute bottom-24 left-12 w-44 h-44 bg-gradient-to-tr from-rose-200/25 to-amber-200/15 rounded-full blur-3xl" />

      <div class="relative z-10 max-w-3xl mx-auto px-6 py-16 flex-1 w-full">
        <div class="bg-white/70 backdrop-blur-md border border-white/70 rounded-3xl shadow-xl shadow-amber-900/5 p-8 md:p-10">
          <div class="space-y-3">
            <p class="text-xs uppercase tracking-[0.25em] text-amber-400">
              {props.subtitle}
            </p>
            <h1 class="text-3xl md:text-4xl font-bold text-stone-800">
              {props.title}
            </h1>
            <p class="text-stone-600 text-base md:text-lg leading-relaxed max-w-3xl">
              {props.description}
            </p>
          </div>

          <div class="mt-8 grid gap-5 sm:grid-cols-2">
            <For each={props.items}>
              {(item) => (
                <MediaCard 
                  item={item}
                />
              )}
            </For>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default MediaPage;

