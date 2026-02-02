import {
  Component,
  For,
  Show,
  createEffect,
  createMemo,
  createSignal,
} from "solid-js";
import type { Routine, Task } from "@/types/api";
import { Icon } from "@/components/shared/Icon";
import {
  faChevronDown,
  faChevronRight,
  faHeart,
  faLeaf,
  faMoon,
  faSun,
} from "@fortawesome/free-solid-svg-icons";
import { buildRoutineGroups } from "@/components/routines/RoutineGroupsList";
import ReadOnlyTaskList from "@/components/tasks/ReadOnlyList";

const getRoutineIcon = (name: string) => {
  const lowerName = name.toLowerCase();
  if (lowerName.includes("morning")) return faSun;
  if (lowerName.includes("evening") || lowerName.includes("night"))
    return faMoon;
  if (lowerName.includes("wellness") || lowerName.includes("health"))
    return faHeart;
  return faLeaf;
};

const parseTimeToMinutes = (
  value: string | null | undefined,
): number | null => {
  if (!value) return null;
  const [hRaw, mRaw] = value.trim().split(":");
  const h = Number.parseInt(hRaw ?? "", 10);
  const m = Number.parseInt(mRaw ?? "", 10);
  if (Number.isNaN(h) || Number.isNaN(m)) return null;
  return h * 60 + m;
};

const sortKeyMinutes = (task: Task): number => {
  const tw = task.time_window ?? undefined;
  const start = parseTimeToMinutes(tw?.start_time ?? null);
  const avail = parseTimeToMinutes(tw?.available_time ?? null);
  const end = parseTimeToMinutes(tw?.end_time ?? null);
  // Match backend intent: start_time > available_time > end-of-day fallback
  return start ?? avail ?? end ?? 24 * 60 + 1;
};

export interface ReadOnlyRoutineGroupsChronologicalListProps {
  tasks: Task[];
  routines: Routine[];
  expandedByDefault?: boolean;
  onTaskClick?: (task: Task) => void;
  onRoutineClick?: (routineDefinitionId: string) => void;
}

export const ReadOnlyRoutineGroupsChronologicalList: Component<
  ReadOnlyRoutineGroupsChronologicalListProps
> = (props) => {
  const groups = createMemo(() =>
    buildRoutineGroups(props.tasks, props.routines),
  );

  const [expanded, setExpanded] = createSignal<Set<string>>(new Set());

  createEffect(() => {
    if (!props.expandedByDefault) return;
    const ids = groups()
      .map((g) => g.routineDefinitionId)
      .filter((id): id is string => Boolean(id));
    setExpanded(new Set(ids));
  });

  const isExpanded = (routineDefinitionId: string) =>
    expanded().has(routineDefinitionId);

  const toggleExpanded = (routineDefinitionId: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(routineDefinitionId)) next.delete(routineDefinitionId);
      else next.add(routineDefinitionId);
      return next;
    });
  };

  return (
    <div class="space-y-3">
      <Show when={groups().length === 0}>
        <p class="text-sm text-stone-500">No routines.</p>
      </Show>
      <For each={groups()}>
        {(group) => {
          const icon = () => getRoutineIcon(group.routineName);
          const routineDefinitionId = () => group.routineDefinitionId;
          const sortedTasks = createMemo(() =>
            [...group.tasks].sort((a, b) => {
              const ka = sortKeyMinutes(a);
              const kb = sortKeyMinutes(b);
              if (ka !== kb) return ka - kb;
              return (a.name ?? "").localeCompare(b.name ?? "");
            }),
          );

          return (
            <div class="bg-white/70 border border-white/70 shadow-lg shadow-amber-900/5 rounded-2xl p-4 backdrop-blur-sm">
              <button
                type="button"
                class="w-full flex items-center gap-3"
                onClick={() => {
                  props.onRoutineClick?.(routineDefinitionId());
                  toggleExpanded(routineDefinitionId());
                }}
                aria-expanded={isExpanded(routineDefinitionId())}
              >
                <Icon icon={icon()} class="w-5 h-5 fill-amber-600" />
                <p class="text-xs uppercase tracking-wide text-amber-700">
                  {group.routineName}
                </p>
                <span class="ml-auto text-[10px] uppercase tracking-wide text-stone-500">
                  {group.totalCount}
                </span>
                <Icon
                  icon={
                    isExpanded(routineDefinitionId())
                      ? faChevronDown
                      : faChevronRight
                  }
                  class="w-3.5 h-3.5 fill-stone-500"
                />
              </button>
              <Show when={isExpanded(routineDefinitionId())}>
                <div class="mt-3">
                  <ReadOnlyTaskList
                    tasks={sortedTasks}
                    onItemClick={props.onTaskClick}
                  />
                </div>
              </Show>
            </div>
          );
        }}
      </For>
    </div>
  );
};

export default ReadOnlyRoutineGroupsChronologicalList;
