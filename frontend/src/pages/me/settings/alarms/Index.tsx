import { Component, For, Show, createEffect, createSignal } from "solid-js";
import { createStore, reconcile } from "solid-js/store";
import { useNavigate } from "@solidjs/router";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import SettingsPage from "@/components/shared/SettingsPage";
import { FormError, Input, Select } from "@/components/forms";
import { useAuth } from "@/providers/auth";
import { authAPI } from "@/utils/api";
import { globalNotifications } from "@/providers/notifications";
import type { AlarmPreset, AlarmType } from "@/types/api";

const AlarmPresetsPage: Component = () => {
  const navigate = useNavigate();
  const { user, refetch } = useAuth();
  const [presets, setPresets] = createStore<AlarmPreset[]>([]);
  const [isSaving, setIsSaving] = createSignal(false);
  const [error, setError] = createSignal("");

  createEffect(() => {
    const current = user();
    if (!current) {
      return;
    }
    const existing = current.settings.alarm_presets ?? [];
    const normalized = existing.map((preset) => ({
      ...preset,
      id: preset.id ?? crypto.randomUUID(),
    }));
    setPresets(reconcile(normalized));
  });

  const updatePreset = (index: number, updates: Partial<AlarmPreset>) => {
    setPresets(index, updates);
  };

  const addPreset = () => {
    setPresets(presets.length, {
      id: crypto.randomUUID(),
      name: "",
      time: "",
      type: "URL" as AlarmType,
      url: "",
    });
  };

  const removePreset = (index: number) => {
    setPresets((items) => items.filter((_, idx) => idx !== index));
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError("");
    try {
      const payload = presets.map((preset) => ({
        id: preset.id ?? null,
        name: preset.name?.trim() || null,
        time: preset.time?.trim() || null,
        type: preset.type ?? "URL",
        url: preset.url?.trim() || "",
      }));
      await authAPI.updateProfile({
        settings: {
          alarm_presets: payload,
        },
      });
      await refetch();
      globalNotifications.addSuccess("Alarm presets updated.");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to save alarm presets.";
      setError(message);
      globalNotifications.addError(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <SettingsPage
      heading="Alarm Presets"
      actionButtons={[
        {
          label: "New preset",
          icon: faPlus,
          onClick: addPreset,
        },
      ]}
      bottomLink={{ label: "Back to Settings", url: "/me/settings" }}
    >
      <div class="space-y-6">
        <p class="text-sm text-stone-600">
          Save reusable alarm configurations (name, time, and optional links) to
          quickly add alarms without retyping details.
        </p>

        <FormError error={error()} />

        <div class="space-y-4">
          <Show when={presets.length === 0}>
            <div class="rounded-2xl border border-dashed border-amber-200 bg-amber-50/40 p-6 text-sm text-amber-900/80">
              No presets yet. Add one to make alarms faster to create.
            </div>
          </Show>

          <For each={presets}>
            {(preset, index) => (
              <div class="rounded-2xl border border-amber-100/80 bg-white/80 p-5 shadow-sm shadow-amber-900/5 space-y-4">
                <div class="grid gap-4 md:grid-cols-2">
                  <Input
                    id={`alarm-preset-name-${index()}`}
                    placeholder="Alarm name (optional)"
                    value={() => preset.name ?? ""}
                    onChange={(value) => updatePreset(index(), { name: value })}
                  />
                  <Input
                    id={`alarm-preset-time-${index()}`}
                    type="time"
                    placeholder="Alarm time (optional)"
                    value={() => preset.time ?? ""}
                    onChange={(value) => updatePreset(index(), { time: value })}
                  />
                  <Select
                    id={`alarm-preset-type-${index()}`}
                    value={() => (preset.type ?? "URL") as AlarmType}
                    onChange={(value) => updatePreset(index(), { type: value })}
                    options={[
                      { value: "URL", label: "Link" },
                      { value: "GENERIC", label: "Generic" },
                    ]}
                    placeholder="Alarm type"
                  />
                  <Input
                    id={`alarm-preset-url-${index()}`}
                    placeholder="Optional link"
                    value={() => preset.url ?? ""}
                    onChange={(value) => updatePreset(index(), { url: value })}
                  />
                </div>
                <div class="flex justify-end">
                  <button
                    type="button"
                    onClick={() => removePreset(index())}
                    class="text-sm font-medium text-rose-600 hover:text-rose-700"
                  >
                    Remove preset
                  </button>
                </div>
              </div>
            )}
          </For>
        </div>

        <div class="flex items-center justify-between gap-3 pt-4 border-t border-amber-100/80">
          <button
            type="button"
            onClick={() => navigate("/me/settings")}
            class="text-sm font-medium text-stone-600 hover:text-stone-700"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving()}
            class="px-6 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 disabled:bg-amber-300 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving() ? "Saving..." : "Save presets"}
          </button>
        </div>
      </div>
    </SettingsPage>
  );
};

export default AlarmPresetsPage;
