import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";

import RecurringEventSeriesList from "@/components/recurring-events/List";
import SettingsPage from "@/components/shared/SettingsPage";
import { calendarEntrySeriesAPI } from "@/utils/api";

const RecurringEventsPage: Component = () => {
  const navigate = useNavigate();
  const [series] = createResource(calendarEntrySeriesAPI.getAll);

  const handleNavigate = (id?: string) => {
    if (!id) return;
    navigate(`/me/settings/recurring-events/${id}`);
  };

  return (
    <SettingsPage heading="Recurring Events">
      <Show
        when={series()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <RecurringEventSeriesList
          series={series()!}
          onItemClick={(item) => handleNavigate(item.id)}
        />
      </Show>
    </SettingsPage>
  );
};

export default RecurringEventsPage;


