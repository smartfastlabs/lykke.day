import { describe, expect, it } from "vitest";
import {
  getRoutineCompletionState,
  getRoutineStatusLabel,
  getRoutineStatusPillClass,
} from "@/components/routines/routineStatus";
import type { TimingStatus } from "@/types/api";

const fmt = (d: Date) =>
  `T${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`;

describe("routine status pill logic", () => {
  it("computes completion state from counts", () => {
    expect(
      getRoutineCompletionState({
        totalCount: 3,
        completedCount: 3,
        puntedCount: 0,
      }),
    ).toBe("complete");

    expect(
      getRoutineCompletionState({
        totalCount: 2,
        completedCount: 0,
        puntedCount: 2,
      }),
    ).toBe("punted");

    expect(
      getRoutineCompletionState({
        totalCount: 0,
        completedCount: 0,
        puntedCount: 0,
      }),
    ).toBe("normal");
  });

  it("overrides timing status when routine is complete", () => {
    expect(
      getRoutineStatusLabel({
        completionState: "complete",
        timingStatus: "past-due",
        nextAvailableTime: null,
        formatTime: fmt,
      }),
    ).toBe("Done");

    expect(
      getRoutineStatusPillClass({
        completionState: "complete",
        timingStatus: "past-due",
      }),
    ).toBe("bg-emerald-100/70 text-emerald-700");
  });

  it("overrides timing status when routine is punted", () => {
    expect(
      getRoutineStatusLabel({
        completionState: "punted",
        timingStatus: "past-due",
        nextAvailableTime: null,
        formatTime: fmt,
      }),
    ).toBe("Punted");

    expect(
      getRoutineStatusPillClass({
        completionState: "punted",
        timingStatus: "active",
      }),
    ).toBe("bg-rose-100/80 text-rose-700");
  });

  it.each([
    ["active", "Active", "bg-emerald-100/70 text-emerald-700"],
    ["available", "Available", "bg-amber-100/80 text-amber-700"],
    ["needs_attention", "Due soon", "bg-amber-100/80 text-amber-700"],
    ["past-due", "Past due", "bg-rose-100/80 text-rose-700"],
    ["inactive", "Soon", "bg-stone-100 text-stone-600"],
    ["hidden", "Later", "bg-stone-100 text-stone-600"],
  ] satisfies Array<[TimingStatus, string, string]>)(
    "maps status=%s to label/pill class",
    (status, label, pillClass) => {
      expect(
        getRoutineStatusLabel({
          completionState: "normal",
          timingStatus: status,
          nextAvailableTime: null,
          formatTime: fmt,
        }),
      ).toBe(label);

      expect(
        getRoutineStatusPillClass({
          completionState: "normal",
          timingStatus: status,
        }),
      ).toBe(pillClass);
    },
  );

  it("uses nextAvailableTime to show a deterministic Starts label", () => {
    const next = new Date("2026-01-01T10:05:00.000Z");

    expect(
      getRoutineStatusLabel({
        completionState: "normal",
        timingStatus: "inactive",
        nextAvailableTime: next,
        formatTime: fmt,
      }),
    ).toBe("Starts T10:05");

    expect(
      getRoutineStatusLabel({
        completionState: "normal",
        timingStatus: "hidden",
        nextAvailableTime: next,
        formatTime: fmt,
      }),
    ).toBe("Starts T10:05");
  });
});
