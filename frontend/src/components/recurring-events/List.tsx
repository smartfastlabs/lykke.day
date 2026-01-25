import { Component } from "solid-js";

import SettingsList from "@/components/shared/SettingsList";
import { CalendarEntrySeries } from "@/types/api";

import RecurringEventSeriesListItem from "./ListItem";

interface RecurringEventSeriesListProps {
  series: CalendarEntrySeries[];
  onItemClick: (series: CalendarEntrySeries) => void;
}

const RecurringEventSeriesList: Component<RecurringEventSeriesListProps> = (
  props
) => {
  return (
    <SettingsList
      items={props.series}
      getItemLabel={(series) => series.name}
      renderItem={(series) => <RecurringEventSeriesListItem series={series} />}
      onItemClick={props.onItemClick}
      searchPlaceholder="Search recurring events"
      emptyStateLabel="No recurring events yet."
    />
  );
};

export default RecurringEventSeriesList;


