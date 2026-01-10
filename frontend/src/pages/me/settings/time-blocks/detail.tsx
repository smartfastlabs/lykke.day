import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import DetailPage from "@/components/shared/DetailPage";
import TimeBlockDefinitionForm from "@/components/time-blocks/Form";
import { timeBlockDefinitionAPI } from "@/utils/api";
import { TimeBlockDefinition } from "@/types/api";

const TimeBlockDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const [timeBlockDefinition] = createResource<TimeBlockDefinition | undefined, string>(
    () => params.id,
    async (id) => {
      return await timeBlockDefinitionAPI.get(id);
    }
  );

  const handleUpdate = async (partialTimeBlockDefinition: Partial<TimeBlockDefinition>) => {
    const current = timeBlockDefinition();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await timeBlockDefinitionAPI.update({
        ...current,
        ...partialTimeBlockDefinition,
        id: current.id,
      });
      navigate("/me/settings/time-blocks");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update time block";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = timeBlockDefinition();
    if (!current || !current.id) return;
    setError("");
    setIsLoading(true);
    try {
      await timeBlockDefinitionAPI.delete(current.id);
      navigate("/me/settings/time-blocks");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete time block";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Show
      when={timeBlockDefinition()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <DetailPage
          heading="Time Block"
          bottomLink={{ label: "Back to Time Blocks", url: "/me/settings/time-blocks" }}
          edit={
            <div class="flex flex-col items-center justify-center px-6 py-8">
              <div class="w-full max-w-xl">
                <TimeBlockDefinitionForm
                  initialData={current()}
                  onSubmit={handleUpdate}
                  isLoading={isLoading()}
                  error={error()}
                />
              </div>
            </div>
          }
          onDelete={handleDelete}
        />
      )}
    </Show>
  );
};

export default TimeBlockDetailPage;

