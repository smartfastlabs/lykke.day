import { Component } from "solid-js";

import { GenericList } from "@/components/shared/GenericList";
import { CalendarEntrySeries } from "@/types/api";

import RecurringEventSeriesListItem from "./ListItem";

interface RecurringEventSeriesListProps {
  series: CalendarEntrySeries[];
  onItemClick: (series: CalendarEntrySeries) => void;
}

const RecurringEventSeriesList: Component<RecurringEventSeriesListProps> = (props) => {
  return (
    <GenericList
      items={props.series}
      renderItem={(series) => <RecurringEventSeriesListItem series={series} />}
      onItemClick={props.onItemClick}
    />
  );
};

export default RecurringEventSeriesList;


