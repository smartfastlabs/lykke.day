import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@solidjs/testing-library";
import type { JSX } from "solid-js";
import type { CurrentUser } from "@/types/api/user";

import LLMSettingsPage from "./Index";

const {
  updateProfileMock,
  listBasePersonalitiesMock,
  getNotificationConfigMock,
  refetchMock,
} = vi.hoisted(() => ({
  updateProfileMock: vi.fn(),
  listBasePersonalitiesMock: vi.fn(),
  getNotificationConfigMock: vi.fn(),
  refetchMock: vi.fn(),
}));

let currentUser: CurrentUser | null = null;

vi.mock("@/providers/auth", () => ({
  useAuth: () => ({
    user: () => currentUser,
    refetch: refetchMock,
  }),
}));

vi.mock("@/utils/api", () => ({
  authAPI: {
    updateProfile: updateProfileMock,
  },
  basePersonalityAPI: {
    list: listBasePersonalitiesMock,
  },
  usecaseConfigAPI: {
    getNotificationConfig: getNotificationConfigMock,
  },
}));

vi.mock("@/providers/notifications", () => ({
  globalNotifications: {
    addSuccess: vi.fn(),
    addError: vi.fn(),
  },
}));

vi.mock("@/components/shared/SettingsPage", () => ({
  default: (props: { children: JSX.Element }) => <div>{props.children}</div>,
}));

describe("LLMSettingsPage base personality select", () => {
  beforeEach(() => {
    updateProfileMock.mockReset();
    listBasePersonalitiesMock.mockReset();
    getNotificationConfigMock.mockReset();
    refetchMock.mockReset();

    currentUser = {
      id: "user-1",
      email: "test@example.com",
      status: "active",
      is_active: true,
      is_superuser: false,
      is_verified: true,
      settings: {
        template_defaults: [],
        llm_provider: "anthropic",
        base_personality_slug: "custom-slug",
        llm_personality_amendments: [],
      },
      created_at: "2026-03-07T00:00:00Z",
      updated_at: null,
    };

    getNotificationConfigMock.mockResolvedValue({
      user_amendments: [],
      rendered_prompt: "",
    });
  });

  it("shows the persisted slug even when it is missing from fetched options", async () => {
    listBasePersonalitiesMock.mockResolvedValue([
      { slug: "default", label: "Default" },
    ]);

    const { container } = render(() => <LLMSettingsPage />);

    await waitFor(() => {
      const select = container.querySelector(
        "#base-personality",
      ) as HTMLSelectElement | null;
      expect(select).toBeTruthy();
      expect(select?.value).toBe("custom-slug");
    });

    const fallbackOption = screen.getByRole("option", { name: "custom-slug" });
    expect((fallbackOption as HTMLOptionElement).value).toBe("custom-slug");
  });

  it("does not duplicate the option when the persisted slug already exists", async () => {
    listBasePersonalitiesMock.mockResolvedValue([
      { slug: "default", label: "Default" },
      { slug: "custom-slug", label: "Custom Slug" },
    ]);

    const { container } = render(() => <LLMSettingsPage />);

    await waitFor(() => {
      const select = container.querySelector(
        "#base-personality",
      ) as HTMLSelectElement | null;
      expect(select).toBeTruthy();
      expect(select?.value).toBe("custom-slug");
    });

    const options = container.querySelectorAll(
      '#base-personality option[value="custom-slug"]',
    );
    expect(options.length).toBe(1);
  });
});
