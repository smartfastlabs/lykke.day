import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import { faArrowRightFromBracket } from "@fortawesome/free-solid-svg-icons";
import SettingsPage, { ActionButton } from "@/components/shared/SettingsPage";
import CalendarList from "@/components/calendars/List";
import { calendarAPI } from "@/utils/api";

const CalendarsPage: Component = () => {
  const navigate = useNavigate();
  const [calendars] = createResource(calendarAPI.getAll);

  const handleNavigate = (id?: string) => {
    if (!id) return;
    navigate(`/me/settings/calendars/${id}`);
  };

  const actionButtons: ActionButton[] = [
    {
      label: "Connect Google Calendar",
      icon: faArrowRightFromBracket,
      onClick: () => {
        window.location.href = "/api/google/login";
      },
    },
  ];

  return (
    <SettingsPage heading="Calendars" actionButtons={actionButtons}>
      <Show
        when={calendars()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <CalendarList
          calendars={calendars()!}
          onItemClick={(calendar) => handleNavigate(calendar.id)}
        />
      </Show>
    </SettingsPage>
  );
};

export default CalendarsPage;

