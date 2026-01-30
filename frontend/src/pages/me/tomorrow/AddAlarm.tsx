import { Component, createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import ModalPage from "@/components/shared/ModalPage";
import FloatingActionButtons from "@/components/shared/FloatingActionButtons";
import { Icon } from "@/components/shared/Icon";
import { faBell } from "@fortawesome/free-solid-svg-icons";
import { FormError, Input, SubmitButton } from "@/components/forms";
import { tomorrowAPI } from "@/utils/api";

const AddTomorrowAlarmPage: Component = () => {
  const navigate = useNavigate();
  const [name, setName] = createSignal("");
  const [time, setTime] = createSignal("07:00");
  const [url, setUrl] = createSignal("");
  const [isSaving, setIsSaving] = createSignal(false);
  const [formError, setFormError] = createSignal("");

  const handleSave = async (event: Event) => {
    event.preventDefault();
    setFormError("");

    const t = time().trim();
    if (!t) {
      setFormError("Time is required.");
      return;
    }

    try {
      setIsSaving(true);
      await tomorrowAPI.addAlarm({
        name: name().trim() || undefined,
        time: t,
        alarm_type: "URL",
        url: url().trim() || "",
      });
      navigate("/me/tomorrow");
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Failed to add alarm.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      <ModalPage
        subtitle="Add an alarm for tomorrow"
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
            placeholder="Alarm name (optional)"
            value={name}
            onChange={setName}
          />
          {/* Using text input to match existing simple patterns */}
          <Input
            id="alarm-time"
            placeholder="HH:MM"
            value={time}
            onChange={setTime}
            required
          />
          <Input
            id="alarm-url"
            placeholder="Link (optional)"
            value={url}
            onChange={setUrl}
          />
          <FormError error={formError()} />
          <div class="flex items-center gap-3">
            <SubmitButton
              isLoading={isSaving()}
              loadingText="Adding..."
              text="Save & return"
            />
            <button
              type="button"
              onClick={() => navigate("/me/tomorrow")}
              disabled={isSaving()}
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

export default AddTomorrowAlarmPage;
