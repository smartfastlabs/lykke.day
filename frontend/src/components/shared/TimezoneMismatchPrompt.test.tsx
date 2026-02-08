import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, fireEvent, waitFor, screen } from "@solidjs/testing-library";

import TimezoneMismatchPrompt, { __test__ } from "./TimezoneMismatchPrompt";

const { updateProfileMock, refetchMock, addSuccessMock, addErrorMock } = vi.hoisted(
  () => ({
    updateProfileMock: vi.fn(),
    refetchMock: vi.fn(),
    addSuccessMock: vi.fn(),
    addErrorMock: vi.fn(),
  }),
);

let userTimezone: string | null = "America/New_York";
let userId = "user-1";

vi.mock("@/providers/auth", () => ({
  useAuth: () => ({
    user: () => ({
      id: userId,
      email: "test@example.com",
      status: "active",
      is_active: true,
      is_superuser: false,
      is_verified: true,
      settings: { timezone: userTimezone, template_defaults: [] },
      created_at: "2026-02-07T00:00:00Z",
      updated_at: null,
    }),
    refetch: refetchMock,
  }),
}));

vi.mock("@/utils/api", () => ({
  authAPI: {
    updateProfile: updateProfileMock,
  },
}));

vi.mock("@/providers/notifications", () => ({
  globalNotifications: {
    addSuccess: addSuccessMock,
    addError: addErrorMock,
  },
}));

describe("TimezoneMismatchPrompt", () => {
  const originalDateTimeFormat = Intl.DateTimeFormat;
  const originalLocalStorage = window.localStorage;

  beforeEach(() => {
    updateProfileMock.mockReset();
    refetchMock.mockReset();
    addSuccessMock.mockReset();
    addErrorMock.mockReset();

    userId = "user-1";
    userTimezone = "America/New_York";
    const store = new Map<string, string>();
    const mockLocalStorage = {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => store.set(key, String(value)),
      removeItem: (key: string) => store.delete(key),
      clear: () => store.clear(),
      key: (index: number) => Array.from(store.keys())[index] ?? null,
      get length() {
        return store.size;
      },
    } as unknown as typeof window.localStorage;

    Object.defineProperty(window, "localStorage", {
      value: mockLocalStorage,
      configurable: true,
    });
  });

  afterEach(() => {
    Intl.DateTimeFormat = originalDateTimeFormat;
    Object.defineProperty(window, "localStorage", {
      value: originalLocalStorage,
      configurable: true,
    });
    vi.restoreAllMocks();
  });

  function setBrowserTimezone(tz: string) {
    Intl.DateTimeFormat = (() =>
      ({
        resolvedOptions: () => ({ timeZone: tz }),
      }) as unknown as Intl.DateTimeFormat) as unknown as typeof Intl.DateTimeFormat;
  }

  it("shows when device timezone differs from user timezone", async () => {
    setBrowserTimezone("America/Los_Angeles");
    render(() => <TimezoneMismatchPrompt />);

    await waitFor(() => {
      expect(screen.getByText("New timezone detected")).toBeTruthy();
    });

    expect(screen.getByText("Use America/Los_Angeles")).toBeTruthy();
    expect(screen.getByText("Keep America/New_York")).toBeTruthy();
  });

  it("does not show after dismissing the same mismatch", async () => {
    setBrowserTimezone("America/Los_Angeles");

    const signature = __test__.makeDismissSignature({
      userId,
      currentUserTimezone: userTimezone,
      detectedTimezone: "America/Los_Angeles",
    });
    __test__.writeDismissedSignature(signature);

    render(() => <TimezoneMismatchPrompt />);

    await waitFor(() => {
      expect(screen.queryByText("New timezone detected")).toBeNull();
    });
  });

  it("updates timezone via /api/me and refetches user when accepted", async () => {
    setBrowserTimezone("America/Los_Angeles");
    updateProfileMock.mockResolvedValue({});

    render(() => <TimezoneMismatchPrompt />);

    await waitFor(() => {
      expect(screen.getByText("New timezone detected")).toBeTruthy();
    });

    await fireEvent.click(screen.getByText("Use America/Los_Angeles"));

    await waitFor(() => {
      expect(updateProfileMock).toHaveBeenCalledWith({
        settings: { timezone: "America/Los_Angeles" },
      });
      expect(refetchMock).toHaveBeenCalled();
      expect(addSuccessMock).toHaveBeenCalled();
    });

    expect(screen.queryByText("Timezone change detected")).toBeNull();
  });

  it("writes dismissal signature when closed", async () => {
    setBrowserTimezone("America/Los_Angeles");
    render(() => <TimezoneMismatchPrompt />);

    await waitFor(() => {
      expect(screen.getByText("New timezone detected")).toBeTruthy();
    });

    await fireEvent.click(
      screen.getByLabelText("Keep account timezone America/New_York"),
    );

    const raw = window.localStorage.getItem(__test__.DISMISSED_SIGNATURES_KEY);
    expect(raw).not.toBeNull();
    expect(raw).toContain("America/New_York");
    expect(raw).toContain("America/Los_Angeles");
  });
});

