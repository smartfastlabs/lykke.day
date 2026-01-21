import { useNavigate } from "@solidjs/router";
import { Component, Show, createSignal } from "solid-js";

import ProfileForm from "@/components/profile/Form";
import ProfilePreview from "@/components/profile/Preview";
import DetailPage from "@/components/shared/DetailPage";
import { useAuth } from "@/providers/auth";
import { globalNotifications } from "@/providers/notifications";
import { authAPI, calendarAPI } from "@/utils/api";
import type { UserProfileUpdate } from "@/types/api/user";

const ProfileSettingsPage: Component = () => {
  const navigate = useNavigate();
  const { user, refetch } = useAuth();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [isResettingCalendars, setIsResettingCalendars] = createSignal(false);

  const handleUpdate = async (payload: UserProfileUpdate) => {
    setError("");
    setIsLoading(true);
    try {
      await authAPI.updateProfile(payload);
      await refetch();
      navigate("/me/settings");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update profile";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetCalendars = async () => {
    if (isResettingCalendars()) return;

    setIsResettingCalendars(true);
    try {
      await calendarAPI.resetSubscriptions();
      globalNotifications.addSuccess(
        "Calendar entries cleared and subscriptions refreshed"
      );
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to refresh calendar subscriptions";
      globalNotifications.addError(message);
    } finally {
      setIsResettingCalendars(false);
    }
  };

  return (
    <Show
      when={user()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <DetailPage
          heading="Profile"
          bottomLink={{ label: "Back to Settings", url: "/me/settings" }}
          preview={<ProfilePreview user={current()} />}
          edit={
            <div class="flex flex-col items-center justify-center px-6 py-8">
              <div class="w-full max-w-3xl">
                <ProfileForm
                  initialData={current()}
                  onSubmit={handleUpdate}
                  isLoading={isLoading()}
                  error={error()}
                />
              </div>
            </div>
          }
          additionalActionButtons={[
            {
              label: isResettingCalendars()
                ? "Resetting..."
                : "Reset calendar sync",
              onClick: handleResetCalendars,
            },
          ]}
        />
      )}
    </Show>
  );
};

export default ProfileSettingsPage;

