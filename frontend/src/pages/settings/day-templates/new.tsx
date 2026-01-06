import { createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import SettingsPage from "@/components/shared/settingsPage";
import { dayTemplateAPI } from "@/utils/api";
import { DayTemplate } from "@/types/api";
import DayTemplateForm from "@/components/dayTemplates/form";

export default function NewDayTemplate() {
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const handleSubmit = async (template: Partial<DayTemplate>) => {
    setError("");
    setIsLoading(true);

    try {
      await dayTemplateAPI.create(template as DayTemplate);
      navigate("/settings/day-templates");
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create day template";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SettingsPage
      heading="Create Day Template"
      bottomLink={{ label: "Back to Day Templates", url: "/settings/day-templates" }}
    >
      <div class="flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-sm">
          <DayTemplateForm
            onSubmit={handleSubmit}
            isLoading={isLoading()}
            error={error()}
          />
        </div>
      </div>
    </SettingsPage>
  );
}

