import { Component, createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import ModalPage from "@/components/shared/ModalPage";
import FloatingActionButtons from "@/components/shared/FloatingActionButtons";
import { useStreamingData } from "@/providers/streamingData";
import { Icon } from "@/components/shared/Icon";
import { faBullseye } from "@fortawesome/free-solid-svg-icons";
import { FormError, Input, SubmitButton } from "@/components/forms";

const AddReminderPage: Component = () => {
  const navigate = useNavigate();
  const { addReminder, isLoading } = useStreamingData();
  const [reminderName, setReminderName] = createSignal("");
  const [isSaving, setIsSaving] = createSignal(false);
  const [formError, setFormError] = createSignal("");

  const handleSave = async (event: Event) => {
    event.preventDefault();
    setFormError("");
    const name = reminderName().trim();
    if (!name) {
      setFormError("Reminder name is required.");
      return;
    }

    try {
      setIsSaving(true);
      await addReminder(name);
      navigate("/me/today");
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Failed to add reminder.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      <ModalPage
        subtitle="Add a quick reminder for today"
        title={
          <div class="flex items-center justify-center gap-3">
            <Icon icon={faBullseye} class="w-6 h-6 fill-amber-600" />
            <p class="text-2xl font-semibold text-stone-800">Add Reminder</p>
          </div>
        }
      >
        <form class="space-y-5" onSubmit={handleSave}>
          <Input
            id="reminder-name"
            placeholder="Reminder name"
            value={reminderName}
            onChange={setReminderName}
            required
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
              onClick={() => navigate("/me/today")}
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

export default AddReminderPage;
