import { Component, createMemo, createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import ModalPage from "@/components/shared/ModalPage";
import FloatingActionButtons from "@/components/shared/FloatingActionButtons";
import { useStreamingData } from "@/providers/streamingData";
import { useAuth } from "@/providers/auth";
import { Icon } from "@/components/shared/Icon";
import { faBell } from "@fortawesome/free-solid-svg-icons";
import { FormError, Input, Select, SubmitButton } from "@/components/forms";
import type { AlarmPreset, AlarmType } from "@/types/api";

const AddAlarmPage: Component = () => {
  const navigate = useNavigate();
  const { addAlarm, isLoading } = useStreamingData();
  const { user } = useAuth();
  const [alarmName, setAlarmName] = createSignal("");
  const [alarmTime, setAlarmTime] = createSignal("");
  const [alarmType, setAlarmType] = createSignal<AlarmType>("URL");
  const [alarmUrl, setAlarmUrl] = createSignal("");
  const [selectedPresetId, setSelectedPresetId] = createSignal("");
  const [isSaving, setIsSaving] = createSignal(false);
  const [formError, setFormError] = createSignal("");

  const formatDefaultAlarmName = (timeValue: string): string => {
    if (!timeValue) {
      return "Alarm";
    }
    const [hourValue, minuteValue] = timeValue.split(":");
    const hours = Number(hourValue);
    const minutes = Number(minuteValue);
    if (Number.isNaN(hours) || Number.isNaN(minutes)) {
      return "Alarm";
    }
    const period = hours >= 12 ? "pm" : "am";
    const hour12 = hours % 12 || 12;
    return `${hour12}:${String(minutes).padStart(2, "0")} ${period} Alarm`;
  };

  const formatPresetLabel = (preset: AlarmPreset): string => {
    const timeLabel = preset.time ? formatDefaultAlarmName(preset.time) : null;
    const nameLabel = preset.name?.trim() || timeLabel || "Untitled alarm";
    const hasUrl = Boolean(preset.url?.trim());
    return hasUrl ? `${nameLabel} · link` : nameLabel;
  };

  const alarmPresets = createMemo<AlarmPreset[]>(
    () => user()?.settings.alarm_presets ?? [],
  );
  const presetOptions = createMemo(() =>
    alarmPresets().map((preset, index) => ({
      value: preset.id ?? `preset-${index}`,
      label: formatPresetLabel(preset),
    })),
  );

  const handlePresetChange = (presetId: string) => {
    setSelectedPresetId(presetId);
    if (!presetId) {
      return;
    }
    const preset = alarmPresets().find(
      (item, index) => (item.id ?? `preset-${index}`) === presetId,
    );
    if (!preset) {
      return;
    }
    setAlarmName(preset.name ?? "");
    setAlarmTime(preset.time ?? "");
    setAlarmType(preset.type ?? "URL");
    setAlarmUrl(preset.url ?? "");
  };

  const handleSave = async (event: Event) => {
    event.preventDefault();
    setFormError("");
    const name = alarmName().trim();
    const time = alarmTime().trim();
    const url = alarmUrl().trim();
    if (!time) {
      setFormError("Alarm time is required.");
      return;
    }

    try {
      setIsSaving(true);
      await addAlarm({
        name: name || undefined,
        time,
        alarmType: alarmType(),
        url: url || undefined,
      });
      navigate("/me");
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Failed to add alarm."
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      <ModalPage
        subtitle="Add an alarm for today"
        title={
          <div class="flex items-center justify-center gap-3">
            <Icon icon={faBell} class="w-6 h-6 fill-amber-600" />
            <p class="text-2xl font-semibold text-stone-800">Add Alarm</p>
          </div>
        }
      >
        <form class="space-y-5" onSubmit={handleSave}>
          <Select
            id="alarm-preset"
            value={selectedPresetId}
            onChange={handlePresetChange}
            options={presetOptions()}
            placeholder="Choose a preset (optional)"
          />
          <Input
            id="alarm-name"
            placeholder="Alarm name (optional)"
            value={alarmName}
            onChange={setAlarmName}
          />
          <p class="text-xs text-stone-500">
            Leave blank to use {formatDefaultAlarmName(alarmTime())}.
          </p>
          <Input
            id="alarm-time"
            type="time"
            placeholder="Alarm time"
            value={alarmTime}
            onChange={setAlarmTime}
            required
          />
          <Select
            id="alarm-type"
            value={alarmType}
            onChange={setAlarmType}
            options={[
              { value: "URL", label: "Link" },
              { value: "GENERIC", label: "Generic" },
            ]}
            placeholder="Alarm type"
            required
          />
          <Input
            id="alarm-url"
            placeholder="Optional link"
            value={alarmUrl}
            onChange={setAlarmUrl}
          />
          <FormError error={formError()} />
          <div class="flex items-center gap-3">
            <SubmitButton
              isLoading={isSaving() || isLoading()}
              loadingText="Adding..."
              text="Save & return"
            />
            <button
              type="button"
              onClick={() => navigate("/me")}
              disabled={isSaving() || isLoading()}
              class="flex-1 h-11 flex items-center justify-center bg-white border border-stone-200 text-stone-700 rounded-lg hover:bg-stone-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
          </div>
        </form>
      </ModalPage>
      <FloatingActionButtons />
    </>
  );
};

export default AddAlarmPage;
