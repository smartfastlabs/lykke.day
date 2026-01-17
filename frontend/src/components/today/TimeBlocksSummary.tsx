import {
  Component,
  Show,
  For,
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

const isSameBlock = (a: TimeBlock | null | undefined, b: TimeBlock): boolean =>
  Boolean(
    a &&
      a.time_block_definition_id === b.time_block_definition_id &&
      a.start_time === b.start_time &&
      a.end_time === b.end_time
  );

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

  const timeRange = createMemo(() => {
    const items = blocks();
    if (items.length === 0) return null;
    const start = Math.min(...items.map((block) => block.start));
    const end = Math.max(...items.map((block) => block.end));
    return { start, end, total: Math.max(end - start, 1) };
  });

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
      <div class="space-y-2">
        <div class="space-y-1">
          <div class="h-2 rounded-full bg-amber-600/20 overflow-hidden flex">
            <For each={blocks()}>
              {(block) => {
                const range = timeRange();
                const width = range
                  ? ((block.end - block.start) / range.total) * 100
                  : 0;
                const isCurrent = isSameBlock(currentBlock(), block);
                const isNext = !isCurrent && isSameBlock(nextBlock(), block);
                return (
                  <div
                    class="h-full transition-colors"
                    classList={{
                      "bg-amber-600/80": isCurrent,
                      "bg-amber-600/60": isNext,
                      "bg-amber-600/40": !isCurrent && !isNext,
                    }}
                    style={{ width: `${width}%` }}
                    title={`${block.name} • ${formatRange(block)}`}
                  />
                );
              }}
            </For>
          </div>
          <div class="flex items-center justify-between text-[10px] text-amber-600/80">
            <span>{formatTime(blocks()[0].start_time)}</span>
            <span>{formatTime(blocks()[blocks().length - 1].end_time)}</span>
          </div>
        </div>

        <div class="flex items-center gap-3 text-[11px] text-amber-600/80">
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
      </div>
    </Show>
  );
};

export default TimeBlocksSummary;
