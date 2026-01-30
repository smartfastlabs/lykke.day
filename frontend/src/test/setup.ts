import "@testing-library/jest-dom";
import { afterEach } from "vitest";
import { cleanup } from "@solidjs/testing-library";

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock WebSocket globally
global.WebSocket = class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  CONNECTING = 0;
  OPEN = 1;
  CLOSING = 2;
  CLOSED = 3;

  url: string;
  readyState: number = 0;
  onopen: ((_event: Event) => void) | null = null;
  onclose: ((_event: CloseEvent) => void) | null = null;
  onmessage: ((_event: MessageEvent) => void) | null = null;
  onerror: ((_event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = 1;
      if (this.onopen) {
        this.onopen(new Event("open"));
      }
    }, 0);
  }

  send(data: string) {
    // Store sent data for testing
    const self = this as unknown as { _sentData?: string[] };
    self._sentData = self._sentData || [];
    self._sentData.push(data);
  }

  close() {
    this.readyState = 3;
    if (this.onclose) {
      this.onclose(new CloseEvent("close"));
    }
  }
} as unknown as typeof WebSocket;

// Mock document.cookie
Object.defineProperty(document, "cookie", {
  writable: true,
  value: "",
});
