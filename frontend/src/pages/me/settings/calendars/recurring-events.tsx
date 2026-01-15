import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";

import RecurringEventSeriesList from "@/components/recurring-events/List";
import SettingsPage from "@/components/shared/SettingsPage";
import { calendarEntrySeriesAPI } from "@/utils/api";

const CalendarRecurringEventsPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();

  const [series] = createResource(params.id, (calendarId) =>
    calendarEntrySeriesAPI.searchByCalendar(calendarId)
  );

  const handleNavigate = (id?: string | null) => {
    if (!id) return;
    navigate(`/me/settings/recurring-events/${id}`);
  };

  return (
    <SettingsPage
      heading="Recurring Events"
      bottomLink={{
        label: "Back to Calendar",
        url: `/me/settings/calendars/${params.id}`,
      }}
    >
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

export default CalendarRecurringEventsPage;


