import { Component, createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import ModalPage from "@/components/shared/ModalPage";
import FloatingActionButtons from "@/components/shared/FloatingActionButtons";
import { useStreamingData } from "@/providers/streamingData";
import { Icon } from "@/components/shared/Icon";
import { faBell } from "@fortawesome/free-solid-svg-icons";
import { FormError, Input, Select, SubmitButton } from "@/components/forms";
import type { AlarmType } from "@/types/api";

const AddAlarmPage: Component = () => {
  const navigate = useNavigate();
  const { addAlarm, isLoading } = useStreamingData();
  const [alarmName, setAlarmName] = createSignal("");
  const [alarmTime, setAlarmTime] = createSignal("");
  const [alarmType, setAlarmType] = createSignal<AlarmType>("URL");
  const [alarmUrl, setAlarmUrl] = createSignal("");
  const [isSaving, setIsSaving] = createSignal(false);
  const [formError, setFormError] = createSignal("");

  const handleSave = async (event: Event) => {
    event.preventDefault();
    setFormError("");
    const name = alarmName().trim();
    const time = alarmTime().trim();
    const url = alarmUrl().trim();
    if (!name) {
      setFormError("Alarm name is required.");
      return;
    }
    if (!time) {
      setFormError("Alarm time is required.");
      return;
    }

    try {
      setIsSaving(true);
      await addAlarm({
        name,
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
          <Input
            id="alarm-name"
            placeholder="Alarm name"
            value={alarmName}
            onChange={setAlarmName}
            required
          />
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
