import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, waitFor } from "@solidjs/testing-library";
import { StreamingDataProvider, useStreamingData } from "./streamingData";
import type { DayContext, Task, TaskStatus } from "@/types/api";

// Mock the API and config modules
vi.mock("@/utils/api", () => ({
  taskAPI: {
    setTaskStatus: vi.fn(),
    recordTaskAction: vi.fn(),
    rescheduleTask: vi.fn(),
    createAdhocTask: vi.fn(),
    deleteTask: vi.fn(),
  },
  routineAPI: {
    setRoutineAction: vi.fn(),
  },
  alarmAPI: {
    addAlarm: vi.fn(),
    snoozeAlarm: vi.fn(),
    cancelAlarm: vi.fn(),
    removeAlarm: vi.fn(),
  },
  calendarEntryAPI: {
    update: vi.fn(),
  },
}));

vi.mock("@/utils/config", () => ({
  getWebSocketBaseUrl: () => "localhost:8080",
  getWebSocketProtocol: () => "ws:",
}));

// Helper to create a mock WebSocket instance with controllable behavior
class ControllableWebSocket {
  static instances: ControllableWebSocket[] = [];
  static OPEN = 1;
  static CLOSED = 3;

  url: string;
  readyState = 0;
  onopen: ((_event: Event) => void) | null = null;
  onclose: ((_event: CloseEvent) => void) | null = null;
  onmessage: ((_event: MessageEvent) => void) | null = null;
  onerror: ((_event: Event) => void) | null = null;
  _sentData: string[] = [];

  constructor(url: string) {
    this.url = url;
    ControllableWebSocket.instances.push(this);
  }

  send(data: string) {
    this._sentData.push(data);
  }

  close() {
    this.readyState = ControllableWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent("close"));
    }
  }

  // Test helper methods
  simulateOpen() {
    this.readyState = ControllableWebSocket.OPEN;
    if (this.onopen) {
      const event = { type: "open" } as Event;
      this.onopen(event);
    }
  }

  simulateMessage(data: unknown) {
    if (this.onmessage) {
      const event = {
        type: "message",
        data: JSON.stringify(data),
      } as MessageEvent;
      this.onmessage(event);
    }
  }

  simulateError() {
    if (this.onerror) {
      const event = { type: "error" } as Event;
      this.onerror(event);
    }
  }

  simulateClose() {
    this.readyState = ControllableWebSocket.CLOSED;
    if (this.onclose) {
      const event = { type: "close" } as CloseEvent;
      this.onclose(event);
    }
  }
}

describe("StreamingDataProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    ControllableWebSocket.instances = [];
    (
      global as unknown as { WebSocket: typeof ControllableWebSocket }
    ).WebSocket = ControllableWebSocket;
    document.cookie = "lykke_auth=test-token";
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
    document.cookie = "";
  });

  const TestComponent = () => {
    const context = useStreamingData();
    return (
      <div>
        <div data-testid="is-loading">{context.isLoading().toString()}</div>
        <div data-testid="is-connected">{context.isConnected().toString()}</div>
        <div data-testid="is-out-of-sync">
          {context.isOutOfSync().toString()}
        </div>
        <div data-testid="tasks-count">{context.tasks().length}</div>
        <div data-testid="events-count">{context.events().length}</div>
      </div>
    );
  };

  describe("WebSocket Connection", () => {
    it("should establish WebSocket connection on mount", async () => {
      render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      expect(ws.url).toContain("ws://localhost:8080/days/today/context");
      expect(ws.url).toContain("token=test-token");
    });

    it("should set isConnected to true when WebSocket opens", async () => {
      const { getByTestId } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();

      await waitFor(() => {
        expect(getByTestId("is-connected").textContent).toBe("true");
      });
    });

    it("should request full sync after connection acknowledgment", async () => {
      render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();
      ws.simulateMessage({
        type: "connection_ack",
        user_id: "test-user",
      });

      await waitFor(() => {
        const sentMessages = ws._sentData.map((d) => JSON.parse(d));
        expect(sentMessages).toContainEqual({
          type: "sync_request",
          since_timestamp: null,
        });
      });
    });

    it("should handle WebSocket errors", async () => {
      const { getByTestId } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();
      ws.simulateError();

      await waitFor(() => {
        expect(getByTestId("is-connected").textContent).toBe("false");
      });
    });

    it("should attempt to reconnect after connection closes", async () => {
      render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();
      ws.simulateClose();

      // Advance timer to trigger reconnection
      await vi.advanceTimersByTimeAsync(3000);

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(2);
      });
    });
  });

  describe("Data Synchronization", () => {
    const mockDayContext: DayContext = {
      day: {
        id: "day-1",
        user_id: "user-1",
        date: "2026-01-15",
        status: "STARTED",
      },
      tasks: [
        {
          id: "task-1",
          user_id: "user-1",
          name: "Test Task",
          status: "NOT_STARTED" as TaskStatus,
          scheduled_date: "2026-01-15",
          type: "WORK",
          category: "WORK",
          frequency: "ONCE",
          description: null,
        },
      ],
      calendar_entries: [],
      events: [],
    };

    it("should update store with full sync response", async () => {
      const { getByTestId } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();
      ws.simulateMessage({
        type: "sync_response",
        day_context: mockDayContext,
        last_audit_log_timestamp: "2026-01-15T12:00:00Z",
      });

      await waitFor(() => {
        expect(getByTestId("tasks-count").textContent).toBe("1");
        expect(getByTestId("is-loading").textContent).toBe("false");
      });
    });

    it("should apply incremental changes for task creation", async () => {
      const { getByTestId } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();

      // First, establish initial state
      ws.simulateMessage({
        type: "sync_response",
        day_context: mockDayContext,
      });

      await waitFor(() => {
        expect(getByTestId("tasks-count").textContent).toBe("1");
      });

      // Then apply incremental change
      const newTask: Task = {
        id: "task-2",
        user_id: "user-1",
        name: "New Task",
        status: "NOT_STARTED",
        scheduled_date: "2026-01-15",
        type: "WORK",
        category: "WORK",
        frequency: "ONCE",
        description: null,
      };

      ws.simulateMessage({
        type: "sync_response",
        changes: [
          {
            change_type: "created",
            entity_type: "task",
            entity_id: "task-2",
            entity_data: newTask,
          },
        ],
      });

      await waitFor(() => {
        expect(getByTestId("tasks-count").textContent).toBe("2");
      });
    });

    it("should apply incremental changes for task update", async () => {
      const { getByTestId } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();

      ws.simulateMessage({
        type: "sync_response",
        day_context: mockDayContext,
      });

      await waitFor(() => {
        expect(getByTestId("tasks-count").textContent).toBe("1");
      });

      const updatedTask: Task = {
        ...mockDayContext.tasks![0],
        name: "Updated Task",
      };

      ws.simulateMessage({
        type: "sync_response",
        changes: [
          {
            change_type: "updated",
            entity_type: "task",
            entity_id: "task-1",
            entity_data: updatedTask,
          },
        ],
      });

      await waitFor(() => {
        expect(getByTestId("tasks-count").textContent).toBe("1");
      });
    });

    it("should apply incremental changes for task deletion", async () => {
      const { getByTestId } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();

      ws.simulateMessage({
        type: "sync_response",
        day_context: mockDayContext,
      });

      await waitFor(() => {
        expect(getByTestId("tasks-count").textContent).toBe("1");
      });

      ws.simulateMessage({
        type: "sync_response",
        changes: [
          {
            change_type: "deleted",
            entity_type: "task",
            entity_id: "task-1",
            entity_data: null,
          },
        ],
      });

      await waitFor(() => {
        expect(getByTestId("tasks-count").textContent).toBe("0");
      });
    });
  });

  describe("Audit Log Events", () => {
    const mockDayContext: DayContext = {
      day: {
        id: "day-1",
        user_id: "user-1",
        date: "2026-01-15",
        status: "STARTED",
      },
      tasks: [
        {
          id: "task-1",
          user_id: "user-1",
          name: "Test Task",
          status: "NOT_STARTED" as TaskStatus,
          scheduled_date: "2026-01-15",
          type: "WORK",
          category: "WORK",
          frequency: "ONCE",
          description: null,
        },
      ],
      calendar_entries: [],
      events: [],
    };

    it("should handle audit log deletion events immediately", async () => {
      const { getByTestId } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();

      ws.simulateMessage({
        type: "sync_response",
        day_context: mockDayContext,
        last_audit_log_timestamp: "2026-01-15T12:00:00Z",
      });

      await waitFor(() => {
        expect(getByTestId("tasks-count").textContent).toBe("1");
      });

      ws.simulateMessage({
        type: "audit_log_event",
        audit_log: {
          id: "audit-1",
          user_id: "user-1",
          activity_type: "TaskDeleted",
          occurred_at: "2026-01-15T12:01:00Z",
          entity_id: "task-1",
          entity_type: "task",
          meta: {},
        },
      });

      await waitFor(() => {
        expect(getByTestId("tasks-count").textContent).toBe("0");
      });
    });

    it("should request incremental sync for created/updated events", async () => {
      const { getByTestId } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();

      ws.simulateMessage({
        type: "sync_response",
        day_context: mockDayContext,
        last_audit_log_timestamp: "2026-01-15T12:00:00Z",
      });

      await waitFor(() => {
        expect(getByTestId("tasks-count").textContent).toBe("1");
      });

      ws.simulateMessage({
        type: "audit_log_event",
        audit_log: {
          id: "audit-1",
          user_id: "user-1",
          activity_type: "TaskCreated",
          occurred_at: "2026-01-15T12:01:00Z",
          entity_id: "task-2",
          entity_type: "task",
          meta: {},
        },
      });

      // Advance timer to trigger debounced sync request
      // Advance slightly more than the debounce delay (500ms) to ensure it fires
      await vi.advanceTimersByTimeAsync(600);

      await waitFor(
        () => {
          const sentMessages = ws._sentData.map((d) => JSON.parse(d));
          const syncRequest = sentMessages.find(
            (m) => m.type === "sync_request" && m.since_timestamp !== null,
          );
          expect(syncRequest).toBeDefined();
          // The timestamp is updated to the audit log's occurred_at before the debounced sync
          expect(syncRequest?.since_timestamp).toBe("2026-01-15T12:01:00Z");
        },
        { timeout: 1000 },
      );
    });

    it("should detect out-of-sync when receiving older events", async () => {
      const { getByTestId } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();

      ws.simulateMessage({
        type: "sync_response",
        day_context: mockDayContext,
        last_audit_log_timestamp: "2026-01-15T12:00:00Z",
      });

      await waitFor(() => {
        expect(getByTestId("is-out-of-sync").textContent).toBe("false");
      });

      // Receive an older event
      ws.simulateMessage({
        type: "audit_log_event",
        audit_log: {
          id: "audit-1",
          user_id: "user-1",
          activity_type: "TaskCreated",
          occurred_at: "2026-01-15T11:00:00Z", // Before last processed
          entity_id: "task-2",
          entity_type: "task",
          meta: {},
        },
      });

      await waitFor(() => {
        expect(getByTestId("is-out-of-sync").textContent).toBe("true");
      });
    });
  });

  describe("Task Status Updates", () => {
    const mockDayContext: DayContext = {
      day: {
        id: "day-1",
        user_id: "user-1",
        date: "2026-01-15",
        status: "STARTED",
      },
      tasks: [
        {
          id: "task-1",
          user_id: "user-1",
          name: "Test Task",
          status: "NOT_STARTED" as TaskStatus,
          scheduled_date: "2026-01-15",
          type: "WORK",
          category: "WORK",
          frequency: "ONCE",
          description: null,
        },
      ],
      calendar_entries: [],
      events: [],
    };

    it("should optimistically update task status", async () => {
      const { taskAPI } = await import("@/utils/api");
      vi.mocked(taskAPI.setTaskStatus).mockResolvedValue({
        ...mockDayContext.tasks![0],
        status: "COMPLETE",
      });

      let context: ReturnType<typeof useStreamingData> | null = null;

      const TestComponent = () => {
        context = useStreamingData();
        return (
          <div>
            <div data-testid="task-status">
              {context.tasks()[0]?.status || "none"}
            </div>
          </div>
        );
      };

      const { getByTestId } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();
      ws.simulateMessage({
        type: "sync_response",
        day_context: mockDayContext,
      });

      await waitFor(() => {
        expect(getByTestId("task-status").textContent).toBe("NOT_STARTED");
      });

      // Update task status
      const statusPromise = context!.setTaskStatus(
        mockDayContext.tasks![0],
        "COMPLETE",
      );
      // Flush timers and microtasks to ensure promise resolves
      await vi.runAllTimersAsync();
      await statusPromise;

      await waitFor(() => {
        expect(getByTestId("task-status").textContent).toBe("COMPLETE");
      });
    });

    it("should rollback on failed task status update", async () => {
      const { taskAPI } = await import("@/utils/api");
      vi.mocked(taskAPI.setTaskStatus).mockRejectedValue(
        new Error("Update failed"),
      );

      let context: ReturnType<typeof useStreamingData> | null = null;

      const TestComponent = () => {
        context = useStreamingData();
        return (
          <div>
            <div data-testid="task-status">
              {context.tasks()[0]?.status || "none"}
            </div>
          </div>
        );
      };

      const { getByTestId } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();
      ws.simulateMessage({
        type: "sync_response",
        day_context: mockDayContext,
      });

      await waitFor(() => {
        expect(getByTestId("task-status").textContent).toBe("NOT_STARTED");
      });

      // Try to update task status
      const statusPromise = context!.setTaskStatus(
        mockDayContext.tasks![0],
        "COMPLETE",
      );
      // Set up error handler immediately to prevent unhandled rejection
      let caughtError: Error | undefined;
      statusPromise.catch((error) => {
        caughtError = error as Error;
      });
      // Flush timers and microtasks to ensure promise resolves/rejects
      await vi.runAllTimersAsync();
      // Wait for the promise to settle
      try {
        await statusPromise;
      } catch (_error) {
        // Error already caught above
      }
      expect(caughtError).toBeDefined();
      expect(caughtError?.message).toBe("Update failed");

      await waitFor(() => {
        expect(getByTestId("task-status").textContent).toBe("NOT_STARTED");
      });
    });
  });

  describe("Context Hook", () => {
    it("should throw error when used outside provider", () => {
      expect(() => {
        render(() => {
          useStreamingData();
          return <div>Test</div>;
        });
      }).toThrow(
        "useStreamingData must be used within a StreamingDataProvider",
      );
    });
  });

  describe("Cleanup", () => {
    it("should close WebSocket and clear timers on unmount", async () => {
      const { unmount } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();

      const closeSpy = vi.spyOn(ws, "close");

      unmount();

      await vi.runAllTimersAsync();

      await waitFor(() => {
        expect(closeSpy).toHaveBeenCalled();
      });
    });

    it("should not attempt to reconnect after unmount", async () => {
      const { unmount } = render(() => (
        <StreamingDataProvider>
          <TestComponent />
        </StreamingDataProvider>
      ));

      await waitFor(() => {
        expect(ControllableWebSocket.instances.length).toBe(1);
      });

      const ws = ControllableWebSocket.instances[0];
      ws.simulateOpen();

      unmount();

      await vi.runAllTimersAsync();

      // Simulate close after unmount
      ws.simulateClose();

      // Advance timer
      await vi.advanceTimersByTimeAsync(3000);

      // Should not create a new WebSocket
      expect(ControllableWebSocket.instances.length).toBe(1);
    });
  });
});
