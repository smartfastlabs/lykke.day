import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, waitFor } from "@solidjs/testing-library";

import MeIndexPage from "./Index";

const navigateMock = vi.fn();

vi.mock("@solidjs/router", async () => {
  const actual = await vi.importActual<typeof import("@solidjs/router")>(
    "@solidjs/router",
  );
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

describe("/me entry route", () => {
  beforeEach(() => {
    navigateMock.mockReset();
    window.localStorage.clear();
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

