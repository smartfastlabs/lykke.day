import { Component } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faCalendarDay } from "@fortawesome/free-solid-svg-icons";
import type { Event } from "@/types/api";

export interface ComingUpCardProps {
  event: Event;
  href: string;
}

export const ComingUpCard: Component<ComingUpCardProps> = (props) => {
  const timeFormatter = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });

  const formatTimeRange = (startIso: string, endIso?: string | null) => {
    const start = timeFormatter.format(new Date(startIso));
    const end = endIso ? timeFormatter.format(new Date(endIso)) : undefined;
    return end ? `${start} – ${end}` : start;
  };

  return (
    <div class="md:col-span-2 bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <Icon icon={faCalendarDay} class="w-5 h-5 fill-amber-600" />
          <p class="text-xs uppercase tracking-wide text-amber-700">Coming Up</p>
        </div>
        <a
          class="text-xs font-semibold text-amber-700 hover:text-amber-800"
          href={props.href}
        >
          See all events
        </a>
      </div>
      <h3 class="text-xl font-semibold text-stone-800 mb-1">
        {props.event.name}
      </h3>
      <p class="text-sm text-stone-500">
        {formatTimeRange(props.event.starts_at, props.event.ends_at)} ·{" "}
        {props.event.platform}
      </p>
      <div class="mt-4 flex gap-2 flex-wrap">
        <span class="px-3 py-1 rounded-full bg-amber-50 text-amber-700 text-xs font-medium">
          {props.event.category}
        </span>
        <span class="px-3 py-1 rounded-full bg-stone-50 text-stone-600 text-xs">
          With {props.event.people?.[0]?.name ?? "team"}
        </span>
      </div>
    </div>
  );
};

