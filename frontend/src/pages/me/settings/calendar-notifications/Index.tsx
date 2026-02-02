import { Component, For, Show, createEffect, createSignal } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import { Input, Select } from "@/components/forms";
import { useAuth } from "@/providers/auth";
import { authAPI } from "@/utils/api";
import { globalNotifications } from "@/providers/notifications";
import type {
  CalendarEntryNotificationChannel,
  CalendarEntryNotificationRule,
  CalendarEntryNotificationSettings,
  UserProfileUpdate,
} from "@/types/api/user";

const CHANNEL_OPTIONS: Array<{
  value: CalendarEntryNotificationChannel;
  label: string;
}> = [
  { value: "TEXT", label: "Text message" },
  { value: "PUSH", label: "Push notification" },
  { value: "KIOSK_ALARM", label: "Kiosk alarm" },
];

const DEFAULT_RULES: CalendarEntryNotificationRule[] = [
  { channel: "TEXT", minutes_before: 10 },
  { channel: "PUSH", minutes_before: 5 },
  { channel: "KIOSK_ALARM", minutes_before: 0 },
];

const CalendarNotificationSettingsPage: Component = () => {
  const { user, refetch } = useAuth();
  const [enabled, setEnabled] = createSignal(true);
  const [rules, setRules] = createSignal<CalendarEntryNotificationRule[]>([]);
  const [isSaving, setIsSaving] = createSignal(false);
  const [error, setError] = createSignal("");

  createEffect(() => {
    const current = user();
    if (!current) return;
    const settings = current.settings.calendar_entry_notification_settings;
    if (!settings) {
      setEnabled(true);
      setRules([...DEFAULT_RULES]);
      return;
    }
    setEnabled(settings.enabled ?? true);
    setRules(settings.rules?.length ? [...settings.rules] : [...DEFAULT_RULES]);
  });

  const updateRule = (index: number, next: Partial<CalendarEntryNotificationRule>) => {
    setRules((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], ...next };
      return updated;
    });
  };

  const addRule = () => {
    setRules((prev) => [...prev, { channel: "PUSH", minutes_before: 5 }]);
  };

  const removeRule = (index: number) => {
    setRules((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      const payload: UserProfileUpdate = {
        settings: {
          calendar_entry_notification_settings: {
            enabled: enabled(),
            rules: rules().map((rule) => ({
              channel: rule.channel,
              minutes_before: Math.max(0, Number(rule.minutes_before) || 0),
            })),
          } satisfies CalendarEntryNotificationSettings,
        },
      };
      await authAPI.updateProfile(payload);
      await refetch();
      globalNotifications.addSuccess("Calendar reminder settings saved");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to save settings";
      setError(message);
      globalNotifications.addError(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <SettingsPage
      heading="Calendar Reminders"
      bottomLink={{ label: "Back to Settings", url: "/me/settings" }}
    >
      <div class="space-y-6">
        <Show when={error()}>
          <div class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            {error()}
          </div>
        </Show>

        <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm">
          <div class="flex items-start justify-between gap-6">
            <div>
              <h2 class="text-lg font-semibold text-stone-800">
                Calendar Entry Reminders
              </h2>
              <p class="text-sm text-stone-500">
                Deterministic reminders for upcoming meetings. Configure the
                channels and lead times.
              </p>
            </div>
            <label class="flex items-center gap-2 text-sm text-stone-600">
              <input
                type="checkbox"
                checked={enabled()}
                onChange={(event) => setEnabled(event.currentTarget.checked)}
                class="h-4 w-4 rounded border-neutral-300 text-stone-900 focus:ring-amber-300"
              />
              Enabled
            </label>
          </div>
        </div>

        <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-base font-semibold text-stone-800">
                Reminder Rules
              </h3>
              <p class="text-sm text-stone-500">
                Each rule sends a reminder before the meeting starts.
              </p>
            </div>
            <button
              type="button"
              onClick={addRule}
              class="rounded-full border border-amber-200 px-4 py-2 text-sm font-medium text-amber-700 hover:border-amber-300 hover:text-amber-800"
            >
              Add rule
            </button>
          </div>

          <div class="space-y-3">
            <For each={rules()}>
              {(rule, index) => (
                <div class="grid gap-3 rounded-xl border border-amber-100/80 bg-amber-50/50 p-4 sm:grid-cols-[1fr_1fr_auto]">
                  <Select<CalendarEntryNotificationChannel>
                    id={`calendar-channel-${index()}`}
                    value={() => rule.channel}
                    onChange={(value) => updateRule(index(), { channel: value })}
                    options={CHANNEL_OPTIONS}
                    placeholder="Channel"
                  />
                  <Input
                    id={`calendar-minutes-${index()}`}
                    type="number"
                    min="0"
                    value={() => String(rule.minutes_before ?? 0)}
                    onChange={(value) =>
                      updateRule(index(), {
                        minutes_before: Math.max(0, Number(value) || 0),
                      })
                    }
                    placeholder="Minutes before"
                  />
                  <button
                    type="button"
                    onClick={() => removeRule(index())}
                    class="rounded-full border border-stone-200 px-3 py-2 text-sm text-stone-600 hover:border-stone-300 hover:text-stone-800"
                  >
                    Remove
                  </button>
                </div>
              )}
            </For>
          </div>
        </div>

        <div class="flex justify-end gap-3 pt-4 border-t">
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving()}
            class="rounded-full bg-stone-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSaving() ? "Saving..." : "Save changes"}
          </button>
        </div>
      </div>
    </SettingsPage>
  );
};

export default CalendarNotificationSettingsPage;
