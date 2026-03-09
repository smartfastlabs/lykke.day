import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@solidjs/testing-library";
import CheckInForm from "@/components/checkins/CheckInForm";

const createCheckIn = vi.fn();
const addSuccess = vi.fn();

vi.mock("@/providers/auth", () => ({
  useAuth: () => ({
    user: () => ({
      settings: {
        status_signals: [
          {
            name: "Energy",
            slug: "energy",
            description: "Current energy",
            goal: { text: "", value: null },
          },
        ],
      },
    }),
  }),
}));

vi.mock("@/utils/api", () => ({
  checkInAPI: {
    create: (payload: unknown) => createCheckIn(payload),
  },
}));

vi.mock("@/providers/notifications", () => ({
  globalNotifications: {
    addSuccess: (message: string) => addSuccess(message),
  },
}));

describe("CheckInForm", () => {
  beforeEach(() => {
    createCheckIn.mockReset();
    addSuccess.mockReset();
  });

  it("shows validation error when text and scores are both empty", async () => {
    render(() => <CheckInForm />);

    await fireEvent.submit(screen.getByRole("button", { name: "Save check-in" }));

    expect(
      await screen.findByText("Add text or rate at least one status signal."),
    ).toBeInTheDocument();
    expect(createCheckIn).not.toHaveBeenCalled();
  });

  it("submits score payload when a status signal is rated", async () => {
    createCheckIn.mockResolvedValue(undefined);
    const onSuccess = vi.fn();
    render(() => <CheckInForm onSuccess={onSuccess} />);

    const scoreInput = document.getElementById("checkin-score-energy");
    expect(scoreInput).toBeTruthy();
    await fireEvent.input(scoreInput!, { target: { value: "3.5" } });
    await fireEvent.submit(screen.getByRole("button", { name: "Save check-in" }));

    await waitFor(() => {
      expect(createCheckIn).toHaveBeenCalledWith({
        text: undefined,
        scores: { energy: 3.5 },
      });
    });
    expect(addSuccess).toHaveBeenCalledWith("Check-in saved.");
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });
});
