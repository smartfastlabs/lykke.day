import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import DetailPage from "@/components/shared/detailPage";
import CalendarForm from "@/components/calendars/form";
import CalendarPreview from "@/components/calendars/preview";
import { calendarAPI } from "@/utils/api";
import { Calendar } from "@/types/api";

const CalendarDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const [calendar] = createResource<Calendar | undefined, string>(
    () => params.id,
    async (id) => calendarAPI.get(id)
  );

  const handleUpdate = async (partialCalendar: Partial<Calendar>) => {
    const current = calendar();
    if (!current?.id) return;

    setError("");
    setIsLoading(true);
    try {
      await calendarAPI.update({
        ...current,
        ...partialCalendar,
        id: current.id,
      });
      navigate("/me/settings/calendars");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update calendar";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = calendar();
    if (!current?.id) return;

    setError("");
    setIsLoading(true);
    try {
      await calendarAPI.delete(current.id);
      navigate("/me/settings/calendars");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete calendar";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Show
      when={calendar()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <DetailPage
          heading="Calendar"
          bottomLink={{ label: "Back to Calendars", url: "/me/settings/calendars" }}
          preview={<CalendarPreview calendar={current()} />}
          edit={
            <div class="flex flex-col items-center justify-center px-6 py-8">
              <div class="w-full max-w-sm space-y-6">
                <CalendarForm
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

export default CalendarDetailPage;

