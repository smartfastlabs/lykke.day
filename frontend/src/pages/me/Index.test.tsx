import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, waitFor } from "@solidjs/testing-library";

import MeIndexPage from "./Index";

const navigateMock = vi.fn();

vi.mock("@solidjs/router", () => ({
  useNavigate: () => navigateMock,
}));

describe("/me entry route", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  beforeEach(() => {
    navigateMock.mockReset();
    window.history.replaceState({}, "", "/me");
  });

  it("always redirects to /me/today", async () => {
    render(() => <MeIndexPage />);

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith("/me/today", { replace: true });
    });
  });

  it("forwards OAuth callback params to backend callback endpoint", async () => {
    const replaceMock = vi.fn();
    vi.stubGlobal("location", {
      ...window.location,
      search: "?state=oauth-state&code=oauth-code&iss=https://accounts.google.com",
      replace: replaceMock,
    });
    render(() => <MeIndexPage />);

    await waitFor(() => {
      expect(navigateMock).not.toHaveBeenCalled();
      expect(replaceMock).toHaveBeenCalledWith(
        "/api/google/callback/login?code=oauth-code&state=oauth-state",
      );
    });
  });

});

