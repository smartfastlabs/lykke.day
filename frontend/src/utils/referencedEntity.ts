import type { Event, Task, BrainDump, Routine } from "@/types/api";
import { getEntityTypeLabel } from "./notification";

export type ReferencedEntity = { entity_type: string; entity_id: string };

export interface ResolvedReferencedEntity extends ReferencedEntity {
  label: string;
  url: string | null;
}

interface DayContextEntities {
  tasks: Task[];
  events: Event[];
  brainDumps: BrainDump[];
  routines: Routine[];
}

/**
 * Resolve a referenced entity to a display label and navigation URL using day context.
 */
export function resolveReferencedEntity(
  entity: ReferencedEntity,
  context: DayContextEntities
): ResolvedReferencedEntity {
  const typeLabel = getEntityTypeLabel(entity.entity_type);
  const id = entity.entity_id;

  const normType = entity.entity_type.toLowerCase().replace(/_/g, "");

  if (normType === "task") {
    const task = context.tasks.find((t) => t.id === id);
    return {
      ...entity,
      label: task?.name ?? `${typeLabel} ${id.slice(0, 8)}`,
      url: "/me/today",
    };
  }
  if (normType === "calendarentry") {
    const event = context.events.find((e) => e.id === id);
    const name = event?.name;
    return {
      ...entity,
      label: name ?? `${typeLabel} ${id.slice(0, 8)}`,
      url: "/me/today",
    };
  }
  if (normType === "braindump" || normType === "brain_dump") {
    const item = context.brainDumps.find((b) => b.id === id);
    const text = item?.text?.slice(0, 40);
    return {
      ...entity,
      label: text ? `${text}${(item?.text?.length ?? 0) > 40 ? "…" : ""}` : `${typeLabel} ${id.slice(0, 8)}`,
      url: `/me/brain-dumps/${id}`,
    };
  }
  if (normType === "routine") {
    const routine = context.routines.find((r) => r.id === id);
    const name = routine?.name;
    return {
      ...entity,
      label: name ?? `${typeLabel} ${id.slice(0, 8)}`,
      url: "/me/today/routines",
    };
  }
  if (normType === "day") {
    return {
      ...entity,
      label: typeLabel,
      url: "/me/today",
    };
  }

  return {
    ...entity,
    label: `${typeLabel} ${id.slice(0, 8)}`,
    url: null,
  };
}
