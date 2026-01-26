import { useNavigate } from "@solidjs/router";
import { Component, Show, createMemo, createSignal } from "solid-js";

import ProfileForm from "@/components/profile/Form";
import SettingsPage from "@/components/shared/SettingsPage";
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
  const [isDirty, setIsDirty] = createSignal(false);

  const serializeProfile = (payload: UserProfileUpdate) =>
    JSON.stringify({
      phone_number: payload.phone_number ?? null,
      status: payload.status,
      is_active: payload.is_active,
      is_superuser: payload.is_superuser,
      is_verified: payload.is_verified,
      settings: {
        timezone: payload.settings.timezone ?? null,
        template_defaults: payload.settings.template_defaults ?? [],
      },
    });

  const initialSignature = createMemo(() => {
    const current = user();
    if (!current) return null;
    const payload: UserProfileUpdate = {
      phone_number: current.phone_number ?? null,
      status: current.status,
      is_active: current.is_active,
      is_superuser: current.is_superuser,
      is_verified: current.is_verified,
      settings: {
        timezone: current.settings.timezone ?? null,
        template_defaults: current.settings.template_defaults ?? [],
      },
    };
    return serializeProfile(payload);
  });

  const handleFormChange = (payload: UserProfileUpdate) => {
    const baseline = initialSignature();
    if (!baseline) return;
    setIsDirty(serializeProfile(payload) !== baseline);
  };

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
        <SettingsPage
          heading="Edit Profile"
          bottomLink={{ label: "Back to Settings", url: "/me/settings" }}
        >
          <div class="space-y-6">
            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Profile
                  </div>
                  <div class="text-lg font-semibold text-stone-800">
                    {current().email}
                  </div>
                  <Show
                    when={isDirty()}
                    fallback={<div class="text-xs text-stone-400">All changes saved</div>}
                  >
                    <div class="inline-flex items-center gap-2 text-xs font-medium text-amber-700">
                      <span class="h-2 w-2 rounded-full bg-amber-500" />
                      Unsaved changes
                    </div>
                  </Show>
                </div>
                <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <button
                    type="submit"
                    form="profile-form"
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full bg-stone-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isLoading() ? "Saving..." : "Save changes"}
                  </button>
                  <button
                    type="button"
                    onClick={handleResetCalendars}
                    disabled={isResettingCalendars()}
                    class="w-full sm:w-auto rounded-full border border-stone-200 bg-white px-5 py-3 text-sm font-semibold text-stone-600 shadow-sm transition hover:border-stone-300 hover:text-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isResettingCalendars() ? "Resetting..." : "Reset calendar sync"}
                  </button>
                </div>
              </div>
            </div>

            <ProfileForm
              formId="profile-form"
              initialData={current()}
              onSubmit={handleUpdate}
              onChange={handleFormChange}
              isLoading={isLoading()}
              error={error()}
              showSubmitButton={false}
            />
          </div>
        </SettingsPage>
      )}
    </Show>
  );
};

export default ProfileSettingsPage;

