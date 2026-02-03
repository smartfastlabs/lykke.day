import { describe, it, expect, vi } from "vitest";
import { render } from "@solidjs/testing-library";
import type { Task } from "@/types/api";
import { RightNowSection } from "@/components/today/RightNowSection";
import { UpcomingSection } from "@/components/today/UpcomingSection";
import { NeedsAttentionSection } from "@/components/today/NeedsAttentionSection";

vi.mock("@/providers/streamingData", () => ({
  useStreamingData: () => ({
    setTaskStatus: vi.fn(),
    snoozeTask: vi.fn(),
  }),
}));

const buildTask = (overrides: Partial<Task> = {}): Task =>
  ({
    id: "task-id",
    name: "Task",
    status: "PENDING",
    timing_status: "past-due",
    scheduled_date: "2026-02-02",
    category: "WORK",
    type: "ADHOC",
    ...overrides,
  }) as Task;

describe("Today sections task filtering", () => {
  it("RightNowSection hides completed and punted past-due tasks", () => {
    const active = buildTask({ id: "active", name: "Active task" });
    const completed = buildTask({
      id: "done",
      name: "Completed task",
      status: "COMPLETE",
    });
    const punted = buildTask({
      id: "punted",
      name: "Punted task",
      status: "PUNT",
    });

    const { queryByText, getByText } = render(() => (
      <RightNowSection events={[]} tasks={[active, completed, punted]} />
    ));

    expect(getByText("Right now")).toBeTruthy();
    expect(getByText("Active task")).toBeTruthy();
    expect(queryByText("Completed task")).toBeNull();
    expect(queryByText("Punted task")).toBeNull();
  });

  it("UpcomingSection hides completed and punted inactive tasks", () => {
    const active = buildTask({
      id: "active",
      name: "Active task",
      timing_status: "inactive",
    });
    const completed = buildTask({
      id: "done",
      name: "Completed task",
      timing_status: "inactive",
      status: "COMPLETE",
    });
    const punted = buildTask({
      id: "punted",
      name: "Punted task",
      timing_status: "inactive",
      status: "PUNT",
    });

    const { queryByText, getByText } = render(() => (
      <UpcomingSection events={[]} tasks={[active, completed, punted]} />
    ));

    expect(getByText("Upcoming")).toBeTruthy();
    expect(getByText("Active task")).toBeTruthy();
    expect(queryByText("Completed task")).toBeNull();
    expect(queryByText("Punted task")).toBeNull();
  });

  it("NeedsAttentionSection hides completed and punted tasks", () => {
    const active = buildTask({
      id: "active",
      name: "Active task",
      timing_status: "needs_attention",
    });
    const completed = buildTask({
      id: "done",
      name: "Completed task",
      timing_status: "needs_attention",
      status: "COMPLETE",
    });
    const punted = buildTask({
      id: "punted",
      name: "Punted task",
      timing_status: "needs_attention",
      status: "PUNT",
    });

    const { queryByText, getByText } = render(() => (
      <NeedsAttentionSection tasks={[active, completed, punted]} />
    ));

    expect(getByText("Needs attention")).toBeTruthy();
    expect(getByText("Active task")).toBeTruthy();
    expect(queryByText("Completed task")).toBeNull();
    expect(queryByText("Punted task")).toBeNull();
  });
});
