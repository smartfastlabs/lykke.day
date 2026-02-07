import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent, waitFor } from "@solidjs/testing-library";
import type { ParentProps } from "solid-js";

import MeIndexPage from "./Index";

let dayValue: unknown = undefined;
const { syncMock, updateDayMock } = vi.hoisted(() => ({
  syncMock: vi.fn(),
  updateDayMock: vi.fn(),
}));

vi.mock("@/providers/streamingData", () => ({
  useStreamingData: () => ({
    day: () => dayValue,
    tasks: () => [],
    events: () => [],
    routines: () => [],
    reminders: () => [],
    alarms: () => [],
    isLoading: () => false,
    isPartLoading: () => false,
    sync: syncMock,
  }),
}));

vi.mock("@/utils/api", () => ({
  dayAPI: {
    updateDay: updateDayMock,
  },
}));

vi.mock("@/pages/me/today/Layout", () => ({
  default: (props: ParentProps) => (
    <div data-testid="today-layout">{props.children}</div>
  ),
}));

vi.mock("@/pages/me/today/Index", () => ({
  default: () => <div data-testid="today-index-view" />,
}));

vi.mock("@/pages/me/today/ThatsAll", () => ({
  default: () => <div data-testid="thats-all-view" />,
}));

describe("/me index page", () => {
  beforeEach(() => {
    syncMock.mockReset();
    updateDayMock.mockReset();
    dayValue = undefined;
  });

  it("renders the /me/today experience when status is STARTED", () => {
    dayValue = {
      id: "day-1",
      date: "2026-02-07",
      status: "STARTED",
    };

    const { getByTestId } = render(() => <MeIndexPage />);
    expect(getByTestId("today-layout")).toBeTruthy();
    expect(getByTestId("today-index-view")).toBeTruthy();
  });

  it("renders the end-of-day view when status is COMPLETE", () => {
    dayValue = {
      id: "day-1",
      date: "2026-02-07",
      status: "COMPLETE",
    };

    const { getByTestId, queryByTestId } = render(() => <MeIndexPage />);
    expect(getByTestId("thats-all-view")).toBeTruthy();
    expect(queryByTestId("today-layout")).toBeNull();
  });

  it("renders a scheduled prompt when status is SCHEDULED", () => {
    dayValue = {
      id: "day-1",
      date: "2026-02-07",
      status: "SCHEDULED",
    };

    const { getByText } = render(() => <MeIndexPage />);
    expect(getByText("Ready when you are")).toBeTruthy();
    expect(getByText("Set intentions (start)")).toBeTruthy();
  });

  it("renders an unscheduled prompt when status is UNSCHEDULED", () => {
    dayValue = {
      id: "day-1",
      date: "2026-02-07",
      status: "UNSCHEDULED",
      template: { id: "template-1" },
    };

    const { getByText } = render(() => <MeIndexPage />);
    expect(getByText("Today isn’t scheduled yet")).toBeTruthy();
    expect(getByText("Schedule today")).toBeTruthy();
  });

  it("schedules today (PATCH status=SCHEDULED) when clicking Schedule today", async () => {
    dayValue = {
      id: "day-1",
      date: "2026-02-07",
      status: "UNSCHEDULED",
      template: { id: "template-1" },
    };
    updateDayMock.mockResolvedValue(dayValue);

    const { getByText } = render(() => <MeIndexPage />);
    await fireEvent.click(getByText("Schedule today"));

    await waitFor(() => {
      expect(updateDayMock).toHaveBeenCalledWith("day-1", { status: "SCHEDULED" });
    });
    expect(syncMock).toHaveBeenCalled();
  });
});

