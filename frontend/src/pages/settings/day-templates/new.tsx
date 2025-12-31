import { createSignal } from "solid-js";
import { useNavigate } from "@solidjs/router";
import Page from "../../../components/shared/layout/page";
import { dayTemplateAPI } from "../../../utils/api";
import { DayTemplate } from "../../../types/api";
import DayTemplateForm from "../../../components/dayTemplates/form";

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
    <Page>
      <div class="min-h-screen bg-neutral-50 flex flex-col items-center justify-center px-6">
        <div class="w-full max-w-sm">
          <h1 class="text-2xl font-medium text-neutral-900 text-center mb-8">
            Create Day Template
          </h1>

          <DayTemplateForm
            onSubmit={handleSubmit}
            isLoading={isLoading()}
            error={error()}
          />
        </div>
      </div>
    </Page>
  );
}

