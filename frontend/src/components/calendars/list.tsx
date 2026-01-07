import { Component } from "solid-js";
import { Calendar } from "@/types/api";
import { GenericList } from "@/components/shared/genericList";
import CalendarListItem from "./listItem";

interface CalendarListProps {
  calendars: Calendar[];
  onItemClick: (calendar: Calendar) => void;
}

const CalendarList: Component<CalendarListProps> = (props) => {
  return (
    <GenericList
      items={props.calendars}
      renderItem={(calendar) => <CalendarListItem calendar={calendar} />}
      onItemClick={props.onItemClick}
    />
  );
};

export default CalendarList;

