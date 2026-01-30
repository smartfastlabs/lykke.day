import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { createWsClient, type DomainEventEnvelope } from "./wsClient";

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
    this.onclose?.(new CloseEvent("close"));
  }

  // Test helpers
  simulateOpen() {
    this.readyState = ControllableWebSocket.OPEN;
    this.onopen?.(new Event("open"));
  }

  simulateMessage(data: unknown) {
    this.onmessage?.({
      type: "message",
      data: JSON.stringify(data),
    } as MessageEvent);
  }

  simulateClose() {
    this.readyState = ControllableWebSocket.CLOSED;
    this.onclose?.(new CloseEvent("close"));
  }
}

describe("wsClient", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    ControllableWebSocket.instances = [];
    (
      globalThis as unknown as { WebSocket: typeof ControllableWebSocket }
    ).WebSocket = ControllableWebSocket;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("connects, routes topic messages, and unsubscribes", async () => {
    const onOpen = vi.fn();
    const onMessage = vi.fn();

    const client = createWsClient<unknown, DomainEventEnvelope>({
      url: "ws://example.test",
      onOpen,
      onMessage,
    });

    // Subscribe before the socket is open: should be sent on open.
    const handler = vi.fn();
    const unsub = client.subscribeTopic("topic-1", handler);

    client.connect();
    expect(ControllableWebSocket.instances.length).toBe(1);

    const ws = ControllableWebSocket.instances[0];
    ws.simulateOpen();

    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(ws._sentData.map((d) => JSON.parse(d))).toContainEqual({
      type: "subscribe",
      topics: ["topic-1"],
    });

    ws.simulateMessage({
      type: "topic_event",
      topic: "topic-1",
      event: { event_type: "Hello", event_data: { ok: true } },
    });

    expect(handler).toHaveBeenCalledWith({
      event_type: "Hello",
      event_data: { ok: true },
    });
    expect(onMessage).not.toHaveBeenCalled(); // topic_event handled internally

    unsub();
    expect(ws._sentData.map((d) => JSON.parse(d))).toContainEqual({
      type: "unsubscribe",
      topics: ["topic-1"],
    });
  });

  it("reconnects and re-subscribes topics", async () => {
    let mounted = true;

    const client = createWsClient({
      url: "ws://example.test",
      reconnectDelayMs: 1000,
      shouldReconnect: () => mounted,
    });

    const handler = vi.fn();
    client.subscribeTopic("topic-1", handler);

    client.connect();
    expect(ControllableWebSocket.instances.length).toBe(1);
    ControllableWebSocket.instances[0].simulateOpen();

    // Force close -> reconnect timer should create a new instance
    ControllableWebSocket.instances[0].simulateClose();
    await vi.advanceTimersByTimeAsync(1000);

    expect(ControllableWebSocket.instances.length).toBe(2);
    const ws2 = ControllableWebSocket.instances[1];
    ws2.simulateOpen();

    // Should re-send subscribe for existing topics on open.
    expect(ws2._sentData.map((d) => JSON.parse(d))).toContainEqual({
      type: "subscribe",
      topics: ["topic-1"],
    });

    // Cleanup should stop reconnect behavior
    mounted = false;
    ws2.simulateClose();
    await vi.advanceTimersByTimeAsync(2000);
    expect(ControllableWebSocket.instances.length).toBe(2);
  });

  it("sendJson returns false when not open", () => {
    const client = createWsClient({ url: "ws://example.test" });
    expect(client.sendJson({ hello: "world" })).toBe(false);
  });
});
