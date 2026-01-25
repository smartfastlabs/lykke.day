import { Component, createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import ModalPage from "@/components/shared/ModalPage";
import FloatingActionButtons from "@/components/shared/FloatingActionButtons";
import { useStreamingData } from "@/providers/streamingData";
import { Icon } from "@/components/shared/Icon";
import { faListCheck } from "@fortawesome/free-solid-svg-icons";
import { FormError, Input, Select, SubmitButton } from "@/components/forms";
import { TaskCategory } from "@/types/api";
import { ALL_TASK_CATEGORIES } from "@/types/api/constants";

const AddAdhocTaskPage: Component = () => {
  const navigate = useNavigate();
  const { addAdhocTask, day, isLoading } = useStreamingData();
  const [taskName, setTaskName] = createSignal("");
  const [taskCategory, setTaskCategory] = createSignal<TaskCategory>("WORK");
  const [isSaving, setIsSaving] = createSignal(false);
  const [formError, setFormError] = createSignal("");

  const handleSave = async (e: Event) => {
    e.preventDefault();
    setFormError("");
    const name = taskName().trim();
    if (!name) {
      setFormError("Task name is required.");
      return;
    }
    if (!day()?.date) {
      setFormError("Day context not loaded yet.");
      return;
    }
    try {
      setIsSaving(true);
      await addAdhocTask(name, taskCategory());
      navigate("/me");
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Failed to add task."
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      <ModalPage
        subtitle="Add a quick task for today"
        title={
          <div class="flex items-center justify-center gap-3">
            <Icon icon={faListCheck} class="w-6 h-6 fill-amber-600" />
            <p class="text-2xl font-semibold text-stone-800">Add Task</p>
          </div>
        }
      >
        <form class="space-y-5" onSubmit={handleSave}>
          <Input
            id="adhoc-task-name"
            placeholder="Task name"
            value={taskName}
            onChange={setTaskName}
            required
          />
          <Select
            id="adhoc-task-category"
            placeholder="Category"
            value={taskCategory}
            onChange={(value) => setTaskCategory(value)}
            options={ALL_TASK_CATEGORIES}
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

export default AddAdhocTaskPage;
