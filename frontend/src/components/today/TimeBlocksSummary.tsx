import {
  Component,
  Show,
  createMemo,
  createSignal,
  onCleanup,
  onMount,
} from "solid-js";
import { DayTemplate } from "@/types/api";
import { getDateString } from "@/utils/dates";

type TimeBlock = NonNullable<DayTemplate["time_blocks"]>[number];

interface TimeBlocksSummaryProps {
  timeBlocks: TimeBlock[];
  dayDate?: string;
}

const normalizeTime = (time: string): string => time.slice(0, 5);

const parseMinutes = (time: string): number => {
  const [hour, minute] = normalizeTime(time).split(":");
  return Number(hour) * 60 + Number(minute);
};

const formatTime = (time: string): string => {
  const [hourStr, minute] = normalizeTime(time).split(":");
  const hour = Number(hourStr);
  const ampm = hour >= 12 ? "p" : "a";
  const hour12 = hour % 12 || 12;
  return `${hour12}:${minute}${ampm}`;
};

const formatRange = (block: TimeBlock): string =>
  `${formatTime(block.start_time)} - ${formatTime(block.end_time)}`;

const TimeBlocksSummary: Component<TimeBlocksSummaryProps> = (props) => {
  const [now, setNow] = createSignal(new Date());

  onMount(() => {
    const interval = setInterval(() => setNow(new Date()), 60000);
    onCleanup(() => clearInterval(interval));
  });

  const blocks = createMemo(() =>
    (props.timeBlocks ?? [])
      .map((block) => {
        const start = parseMinutes(block.start_time);
        const end = Math.max(parseMinutes(block.end_time), start + 1);
        return { ...block, start, end };
      })
      .sort((a, b) => a.start - b.start)
  );

  const isToday = createMemo(() =>
    props.dayDate ? props.dayDate === getDateString() : false
  );

  const currentBlock = createMemo(() => {
    if (!isToday()) return null;
    const nowMinutes = now().getHours() * 60 + now().getMinutes();
    return blocks().find(
      (block) => nowMinutes >= block.start && nowMinutes < block.end
    );
  });

  const nextBlock = createMemo(() => {
    const items = blocks();
    if (items.length === 0) return null;
    if (!isToday()) return items[0];
    const nowMinutes = now().getHours() * 60 + now().getMinutes();
    return items.find((block) => block.start > nowMinutes) ?? null;
  });

  return (
    <Show when={blocks().length > 0}>
      <div class="flex flex-wrap items-center gap-2 text-[11px] text-amber-600/80">
        <Show
          when={currentBlock()}
          fallback={
            <span class="text-amber-600/80">
              <span class="font-medium">Current:</span> No active block
            </span>
          }
        >
          {(block) => (
            <span>
              <span class="font-medium">Current:</span> {block().name} ({formatRange(block())})
            </span>
          )}
        </Show>
        <span class="text-amber-600/60">•</span>
        <Show
          when={nextBlock()}
          fallback={
            <span class="text-amber-600/80">
              <span class="font-medium">Next:</span> No upcoming block
            </span>
          }
        >
          {(block) => (
            <span>
              <span class="font-medium">Next:</span> {block().name} ({formatRange(block())})
            </span>
          )}
        </Show>
      </div>
    </Show>
  );
};

export default TimeBlocksSummary;
