import { Component, createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import ModalPage from "@/components/shared/ModalPage";
import FloatingActionButtons from "@/components/shared/FloatingActionButtons";
import { Icon } from "@/components/shared/Icon";
import { faListCheck } from "@fortawesome/free-solid-svg-icons";
import { FormError, Input, Select, SubmitButton } from "@/components/forms";
import { TaskCategory } from "@/types/api";
import { ALL_TASK_CATEGORIES } from "@/types/api/constants";
import { taskAPI, tomorrowAPI } from "@/utils/api";

const AddTomorrowAdhocTaskPage: Component = () => {
  const navigate = useNavigate();
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

    try {
      setIsSaving(true);
      const day = await tomorrowAPI.ensureScheduled();
      await taskAPI.createAdhocTask({
        scheduled_date: day.date,
        name,
        category: taskCategory(),
      });
      navigate("/me/tomorrow");
    } catch (error) {
      setFormError(
        error instanceof Error ? error.message : "Failed to add task.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      <ModalPage
        subtitle="Add a quick task for tomorrow"
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

export default AddTomorrowAdhocTaskPage;
