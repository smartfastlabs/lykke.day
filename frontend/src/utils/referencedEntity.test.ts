import { describe, expect, it } from "vitest";
import { resolveReferencedEntity, type ReferencedEntity } from "@/utils/referencedEntity";
import type { BrainDump, Event, Routine, Task } from "@/types/api";

const context = {
  tasks: [{ id: "task-1", name: "Task One" } as unknown as Task],
  events: [{ id: "event-1", name: "Event One" } as unknown as Event],
  brainDumps: [
    {
      id: "bd-1",
      text: "This is a very long brain dump note that should be truncated in labels",
    } as unknown as BrainDump,
  ],
  routines: [{ id: "routine-1", name: "Routine One" } as unknown as Routine],
};

describe("resolveReferencedEntity", () => {
  it("resolves known task references", () => {
    const ref: ReferencedEntity = { entity_type: "task", entity_id: "task-1" };
    expect(resolveReferencedEntity(ref, context)).toMatchObject({
      label: "Task One",
      url: "/me/today",
    });
  });

  it("resolves brain dump with truncation and route", () => {
    const ref: ReferencedEntity = { entity_type: "brain_dump", entity_id: "bd-1" };
    const resolved = resolveReferencedEntity(ref, context);
    expect(resolved.url).toBe("/me/brain-dumps/bd-1");
    expect(resolved.label.endsWith("…")).toBe(true);
  });

  it("falls back for unknown entity types", () => {
    const ref: ReferencedEntity = {
      entity_type: "something_new",
      entity_id: "1234567890",
    };
    expect(resolveReferencedEntity(ref, context)).toMatchObject({
      label: "something new 12345678",
      url: null,
    });
  });
});
