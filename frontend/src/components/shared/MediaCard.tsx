import { Component, Show } from "solid-js";

export interface MediaItem {
  title: string;
  creator: string;
  summary: string;
  url: string;
  vibe?: string;
  thumbnail: string;
}

interface MediaCardProps {
  item: MediaItem;
  fallbackImage?: string;
}

const MediaCard: Component<MediaCardProps> = (props) => {
  const fallback = props.fallbackImage || "https://placehold.co/240x135?text=No+Image";

  return (
    <a
      href={props.item.url}
      target="_blank"
      rel="noreferrer"
      class="group bg-white border border-amber-100/60 rounded-2xl p-5 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 flex flex-col gap-4 cursor-pointer no-underline"
    >
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-center w-full h-56 overflow-hidden">
          <img
            src={props.item.thumbnail}
            alt={`${props.item.title} thumbnail`}
            class="max-h-full object-contain shadow-sm shadow-stone-900/10"
            loading="lazy"
            onError={(event) => {
              event.currentTarget.onerror = null;
              event.currentTarget.src = fallback;
            }}
          />
        </div>
        <div class="space-y-2">
          <Show when={props.item.vibe}>
            <p class="inline-flex items-center px-2 py-1 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800">
              {props.item.vibe}
            </p>
          </Show>
          <h2 class="text-lg font-semibold text-stone-800 leading-snug group-hover:text-amber-700 transition-colors">
            {props.item.title}
          </h2>
          <p class="text-sm text-stone-500">{props.item.creator}</p>
          <p class="text-sm text-stone-600 leading-relaxed">
            {props.item.summary}
          </p>
        </div>
      </div>
    </a>
  );
};

export default MediaCard;

