import { Component } from "solid-js";
import { Calendar } from "@/types/api";
import SettingsList from "@/components/shared/SettingsList";
import CalendarListItem from "./ListItem";

interface CalendarListProps {
  calendars: Calendar[];
  onItemClick: (calendar: Calendar) => void;
}

const CalendarList: Component<CalendarListProps> = (props) => {
  return (
    <SettingsList
      items={props.calendars}
      getItemLabel={(calendar) => calendar.name}
      renderItem={(calendar) => <CalendarListItem calendar={calendar} />}
      onItemClick={props.onItemClick}
      searchPlaceholder="Search calendars"
      emptyStateLabel="No calendars connected yet."
    />
  );
};

export default CalendarList;
