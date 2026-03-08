import { describe, expect, it, vi } from "vitest";
import { createMeMenuActions } from "@/components/shared/meMenuActions";

describe("createMeMenuActions", () => {
  it("creates the expected actions and routes", () => {
    const close = vi.fn();
    const navigate = vi.fn();
    const onRefresh = vi.fn();

    const actions = createMeMenuActions({ close, navigate, onRefresh });

    expect(actions.map((action) => action.label)).toEqual([
      "Brain dumps",
      "Notifications",
      "Messages",
      "Tomorrow",
      "Events",
      "Edit day",
      "Refresh",
      "Navigation",
      "Settings",
    ]);

    const actionRouteMap: Record<string, string> = {
      "Brain dumps": "/me/today/brain-dumps",
      Notifications: "/me/today/notifications",
      Messages: "/me/today/messages",
      Tomorrow: "/me/tomorrow",
      Events: "/me/today/events",
      "Edit day": "/me/today/edit",
      Navigation: "/me/nav",
      Settings: "/me/settings",
    };

    Object.entries(actionRouteMap).forEach(([label, route]) => {
      const action = actions.find((candidate) => candidate.label === label);
      expect(action).toBeTruthy();
      action?.onClick();
      expect(navigate).toHaveBeenCalledWith(route);
    });

    expect(close).toHaveBeenCalledTimes(8);
    expect(onRefresh).not.toHaveBeenCalled();
  });

  it("calls provided onRefresh for Refresh action", () => {
    const close = vi.fn();
    const navigate = vi.fn();
    const onRefresh = vi.fn();

    const actions = createMeMenuActions({ close, navigate, onRefresh });
    const refreshAction = actions.find((action) => action.label === "Refresh");

    expect(refreshAction).toBeTruthy();
    refreshAction?.onClick();

    expect(close).toHaveBeenCalledTimes(1);
    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(navigate).not.toHaveBeenCalled();
  });

  it("falls back to window reload when onRefresh is missing", () => {
    const close = vi.fn();
    const navigate = vi.fn();
    const reload = vi.fn();

    vi.stubGlobal("window", {
      location: { reload },
    });

    const actions = createMeMenuActions({ close, navigate });
    const refreshAction = actions.find((action) => action.label === "Refresh");

    expect(refreshAction).toBeTruthy();
    refreshAction?.onClick();

    expect(close).toHaveBeenCalledTimes(1);
    expect(reload).toHaveBeenCalledTimes(1);
    expect(navigate).not.toHaveBeenCalled();
  });
});
