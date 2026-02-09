import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, waitFor } from "@solidjs/testing-library";

import MeIndexPage from "./Index";

const navigateMock = vi.fn();

vi.mock("@solidjs/router", () => ({
  useNavigate: () => navigateMock,
}));

const createLocalStorageMock = () => {
  const store = new Map<string, string>();
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => {
      store.clear();
    },
  };
};

describe("/me entry route", () => {
  beforeEach(() => {
    navigateMock.mockReset();

    // Ensure a stable localStorage API regardless of test environment.
    Object.defineProperty(window, "localStorage", {
      value: createLocalStorageMock(),
      configurable: true,
    });
  });

  it("redirects to the last stored /me path", async () => {
    window.localStorage.setItem("lykke:last-me-path", "/me/settings/profile");

    render(() => <MeIndexPage />);

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith("/me/settings/profile", {
        replace: true,
      });
    });
  });

  it("falls back to /me/today when no last path is stored", async () => {
    render(() => <MeIndexPage />);

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith("/me/today", { replace: true });
    });
  });

  it("ignores invalid stored values and falls back", async () => {
    window.localStorage.setItem("lykke:last-me-path", "https://evil.example/");

    render(() => <MeIndexPage />);

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith("/me/today", { replace: true });
    });
  });
});

