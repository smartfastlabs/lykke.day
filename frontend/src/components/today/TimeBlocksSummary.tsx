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

const isSameBlock = (a: TimeBlock | null, b: TimeBlock): boolean =>
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
      <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-5 backdrop-blur-sm space-y-4">
        <div class="flex items-center justify-between">
          <p class="text-xs uppercase tracking-wide text-stone-500">
            Time Blocks
          </p>
          <Show when={currentBlock()}>
            <span class="text-[11px] font-semibold uppercase tracking-wide text-amber-700 bg-amber-50/80 rounded-full px-2 py-0.5">
              In progress
            </span>
          </Show>
        </div>

        <div class="space-y-2">
          <div class="h-3 rounded-full bg-stone-100/80 overflow-hidden flex">
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
                      "bg-amber-500/70": isCurrent,
                      "bg-amber-300/60": isNext,
                      "bg-stone-200/70": !isCurrent && !isNext,
                      "ring-1 ring-amber-500/50": isCurrent,
                    }}
                    style={{ width: `${width}%` }}
                    title={`${block.name} • ${formatRange(block)}`}
                  />
                );
              }}
            </For>
          </div>
          <div class="flex items-center justify-between text-[11px] text-stone-400">
            <span>{formatTime(blocks()[0].start_time)}</span>
            <span>{formatTime(blocks()[blocks().length - 1].end_time)}</span>
          </div>
        </div>

        <div class="grid gap-2 sm:grid-cols-2">
          <div class="rounded-lg border border-stone-100 bg-white/80 px-3 py-2">
            <p class="text-[11px] uppercase tracking-wide text-stone-400">
              Current
            </p>
            <Show
              when={currentBlock()}
              fallback={
                <p class="text-sm text-stone-500">No active block</p>
              }
            >
              {(block) => (
                <>
                  <p class="text-sm font-semibold text-stone-800">
                    {block().name}
                  </p>
                  <p class="text-xs text-stone-500">{formatRange(block())}</p>
                </>
              )}
            </Show>
          </div>
          <div class="rounded-lg border border-stone-100 bg-white/80 px-3 py-2">
            <p class="text-[11px] uppercase tracking-wide text-stone-400">
              Next
            </p>
            <Show
              when={nextBlock()}
              fallback={<p class="text-sm text-stone-500">No upcoming block</p>}
            >
              {(block) => (
                <>
                  <p class="text-sm font-semibold text-stone-800">
                    {block().name}
                  </p>
                  <p class="text-xs text-stone-500">{formatRange(block())}</p>
                </>
              )}
            </Show>
          </div>
        </div>
      </div>
    </Show>
  );
};

export default TimeBlocksSummary;
