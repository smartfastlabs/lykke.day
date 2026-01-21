// TimeBadge.tsx
import type { Component } from "solid-js";

type TimeBadgeProps = {
  value: Date;
  locale?: string;
};

const TimeBadge: Component<TimeBadgeProps> = (props) => {
  const locale = () => props.locale ?? "en-US";

  const timeText = () =>
    new Intl.DateTimeFormat(locale(), {
      hour: "numeric",
      minute: "numeric",
      hour12: true,
    }).format(props.value);

  return (
    <time class="w-[80px] items-center rounded-lg border border-gray-300 bg-white px-3 py-1 text-xs text-gray-800 shadow-sm">
      {timeText()}
    </time>
  );
};

export default TimeBadge;
