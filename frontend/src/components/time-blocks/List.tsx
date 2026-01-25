import { Component } from "solid-js";
import { TimeBlockDefinition } from "@/types/api";
import SettingsList from "@/components/shared/SettingsList";
import TimeBlockDefinitionListItem from "./ListItem";

interface ListProps {
  timeBlockDefinitions: TimeBlockDefinition[];
  onItemClick: (timeBlockDefinition: TimeBlockDefinition) => void;
}

const TimeBlockDefinitionList: Component<ListProps> = (props) => {
  return (
    <SettingsList
      items={props.timeBlockDefinitions}
      getItemLabel={(timeBlockDefinition) => timeBlockDefinition.name}
      renderItem={(timeBlockDefinition) => (
        <TimeBlockDefinitionListItem timeBlockDefinition={timeBlockDefinition} />
      )}
      onItemClick={props.onItemClick}
      searchPlaceholder="Search time blocks"
      emptyStateLabel="No time blocks yet."
    />
  );
};

export default TimeBlockDefinitionList;

