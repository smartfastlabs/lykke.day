import { beforeEach, describe, expect, it, vi } from "vitest";

const { addErrorMock } = vi.hoisted(() => ({
  addErrorMock: vi.fn(),
}));

vi.mock("@/providers/notifications", () => ({
  globalNotifications: {
    addError: addErrorMock,
    addSuccess: vi.fn(),
  },
}));

import { ApiRequestError, usecaseConfigAPI } from "@/utils/api";

const makeJsonResponse = (status: number, body: unknown) =>
  ({
    status,
    ok: status >= 200 && status < 300,
    json: vi.fn().mockResolvedValue(body),
  });

describe("usecaseConfigAPI generic usecase helpers", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.stubGlobal("fetch", vi.fn());
  });

  it("returns default config when getConfigForUseCase receives 404", async () => {
    vi.mocked(fetch as any).mockResolvedValueOnce(
      makeJsonResponse(404, { detail: "Not found" }) as any,
    );

    const result = await usecaseConfigAPI.getConfigForUseCase("todays_status");

    expect(result).toEqual({ user_amendments: [] });
    expect(fetch).toHaveBeenCalledWith("/api/usecase-configs/todays_status", {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });
  });

  it("returns null when getLLMSnapshotPreviewForUseCase receives 404", async () => {
    vi.mocked(fetch as any).mockResolvedValueOnce(
      makeJsonResponse(404, { detail: "Not found" }) as any,
    );

    const result =
      await usecaseConfigAPI.getLLMSnapshotPreviewForUseCase("todays_status");

    expect(result).toBeNull();
    expect(fetch).toHaveBeenCalledWith(
      "/api/usecase-configs/todays_status/llm-preview",
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      },
    );
  });

  it("rethrows non-404 errors from getConfigForUseCase", async () => {
    vi.mocked(fetch as any).mockResolvedValueOnce(
      makeJsonResponse(500, { detail: "server exploded" }) as any,
    );

    await expect(
      usecaseConfigAPI.getConfigForUseCase("todays_status"),
    ).rejects.toMatchObject({
      name: "ApiRequestError",
      status: 500,
      message: "server exploded",
    } satisfies Partial<ApiRequestError>);
  });
});
