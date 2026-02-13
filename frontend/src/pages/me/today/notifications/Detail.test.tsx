import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render } from "@solidjs/testing-library";
import type { PushNotification } from "@/types/api";
import TodayNotificationDetailPage from "./Detail";

let paramId = "notif-1";
let notificationsData: PushNotification[] = [];
let loading = false;
const loadNotificationsMock = vi.fn(async () => undefined);

vi.mock("@solidjs/router", () => ({
  useParams: () => ({ id: paramId }),
}));

vi.mock("@/providers/streamingData", () => ({
  useStreamingData: () => ({
    notifications: () => notificationsData,
    notificationsLoading: () => loading,
    loadNotifications: loadNotificationsMock,
  }),
}));

vi.mock("@/components/notifications/ReferencedEntitiesView", () => ({
  default: (props: { referencedEntities: unknown[] }) => (
    <div data-testid="refs-view">{props.referencedEntities.length}</div>
  ),
}));

vi.mock("@/components/notifications/LLMDebugView", () => ({
  default: () => <div data-testid="debug-view">debug-view</div>,
}));

vi.mock("@/pages/me/today/Layout", () => ({
  default: (props: { children: unknown }) => <div>{props.children}</div>,
}));

const buildNotification = (
  overrides: Partial<PushNotification> = {},
): PushNotification =>
  ({
    id: "notif-1",
    content: '{"body":"Body text"}',
    sent_at: "2026-02-12T12:00:00Z",
    status: "success",
    message: "",
    referenced_entities: [{ entity_type: "task", entity_id: "task-1" }],
    ...overrides,
  }) as PushNotification;

describe("TodayNotificationDetailPage", () => {
  beforeEach(() => {
    paramId = "notif-1";
    notificationsData = [];
    loading = false;
    loadNotificationsMock.mockClear();
  });

  it("renders item view by default and falls back to payload body text", () => {
    notificationsData = [buildNotification()];

    const { getByText, getByTestId, queryByTestId } = render(() => (
      <TodayNotificationDetailPage />
    ));

    expect(loadNotificationsMock).toHaveBeenCalled();
    expect(getByText("Body text")).toBeTruthy();
    expect(getByText("LLM Debug")).toBeTruthy();
    expect(getByTestId("refs-view").textContent).toBe("1");
    expect(queryByTestId("debug-view")).toBeNull();
  });

  it("toggles between item and debug views", async () => {
    notificationsData = [buildNotification()];
    const { getByText, getByTestId, queryByTestId } = render(() => (
      <TodayNotificationDetailPage />
    ));

    await fireEvent.click(getByText("LLM Debug"));

    expect(getByText("Back to items")).toBeTruthy();
    expect(getByTestId("debug-view")).toBeTruthy();
    expect(queryByTestId("refs-view")).toBeNull();
  });

  it("shows fallback message when payload has no message/title/body", () => {
    notificationsData = [
      buildNotification({
        content: '{"foo":"bar"}',
        message: "",
      }),
    ];

    const { getByText } = render(() => <TodayNotificationDetailPage />);
    expect(getByText("No message content available.")).toBeTruthy();
  });
});
