import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createMemo, createResource, createSignal } from "solid-js";
import SettingsPage from "@/components/shared/SettingsPage";
import CalendarForm, { CalendarWithCategory } from "@/components/calendars/Form";
import CalendarPreview from "@/components/calendars/Preview";
import { calendarAPI } from "@/utils/api";

const CalendarDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [isToggling, setIsToggling] = createSignal(false);
  const [isResyncing, setIsResyncing] = createSignal(false);
  const [isDirty, setIsDirty] = createSignal(false);

  const [calendar, { mutate }] = createResource<
    CalendarWithCategory | undefined,
    string
  >(
    () => params.id,
    async (id) => calendarAPI.get(id) as Promise<CalendarWithCategory>
  );

  const serializeCalendar = (value: Partial<CalendarWithCategory>) =>
    JSON.stringify({
      name: (value.name ?? "").trim(),
      auth_token_id: (value.auth_token_id ?? "").trim(),
      default_event_category: value.default_event_category ?? null,
    });

  const initialSignature = createMemo(() => {
    const current = calendar();
    if (!current) return null;
    return serializeCalendar(current);
  });

  const handleFormChange = (value: Partial<CalendarWithCategory>) => {
    const baseline = initialSignature();
    if (!baseline) return;
    setIsDirty(serializeCalendar(value) !== baseline);
  };

  const handleUpdate = async (partialCalendar: Partial<CalendarWithCategory>) => {
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

  const handleToggleSubscription = async () => {
    const current = calendar();
    if (!current?.id) return;

    setError("");
    setIsToggling(true);
    try {
      const hasSubscription =
        current.sync_enabled ?? Boolean(current.sync_subscription);
      const updated = hasSubscription
        ? await calendarAPI.unsubscribe(current.id)
        : await calendarAPI.subscribe(current.id);
      mutate(updated);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to toggle sync";
      setError(message);
    } finally {
      setIsToggling(false);
    }
  };

  const handleResync = async () => {
    const current = calendar();
    if (!current?.id) return;

    setError("");
    setIsResyncing(true);
    try {
      const updated = await calendarAPI.resync(current.id);
      mutate(updated);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to resync calendar";
      setError(message);
    } finally {
      setIsResyncing(false);
    }
  };

  return (
    <Show
      when={calendar()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <SettingsPage
          heading="Edit Calendar"
          bottomLink={{ label: "Back to Calendars", url: "/me/settings/calendars" }}
        >
          <div class="space-y-6">
            <div class="rounded-xl border border-amber-100/80 bg-white/90 p-5 shadow-sm">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div class="space-y-1">
                  <div class="text-xs uppercase tracking-wide text-stone-400">
                    Calendar
                  </div>
                  <div class="text-lg font-semibold text-stone-800">
                    {current().name}
                  </div>
                  <Show
                    when={isDirty()}
                    fallback={<div class="text-xs text-stone-400">All changes saved</div>}
                  >
                    <div class="inline-flex items-center gap-2 text-xs font-medium text-amber-700">
                      <span class="h-2 w-2 rounded-full bg-amber-500" />
                      Unsaved changes
                    </div>
                  </Show>
                </div>
                <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <button
                    type="submit"
                    form="calendar-form"
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full bg-stone-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isLoading() ? "Saving..." : "Save changes"}
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      navigate(`/me/settings/calendars/${current().id}/recurring-events`)
                    }
                    class="w-full sm:w-auto rounded-full border border-stone-200 bg-white px-5 py-3 text-sm font-semibold text-stone-600 shadow-sm transition hover:border-stone-300 hover:text-stone-800"
                  >
                    Recurring events
                  </button>
                  <button
                    type="button"
                    onClick={handleDelete}
                    disabled={isLoading()}
                    class="w-full sm:w-auto rounded-full border border-stone-200 bg-white px-5 py-3 text-sm font-semibold text-stone-600 shadow-sm transition hover:border-stone-300 hover:text-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Delete calendar
                  </button>
                </div>
              </div>
            </div>

            <div class="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <CalendarForm
                formId="calendar-form"
                initialData={current()}
                onSubmit={handleUpdate}
                onChange={handleFormChange}
                isLoading={isLoading()}
                error={error()}
                showSubmitButton={false}
              />
              <CalendarPreview
                calendar={current()}
                onToggleSync={handleToggleSubscription}
                isToggling={isToggling()}
                onResync={handleResync}
                isResyncing={isResyncing()}
              />
            </div>
          </div>
        </SettingsPage>
      )}
    </Show>
  );
};

export default CalendarDetailPage;

