import { Component } from "solid-js";
import { TimeBlockDefinition } from "@/types/api";
import { GenericList } from "@/components/shared/GenericList";
import TimeBlockDefinitionListItem from "./ListItem";

interface ListProps {
  timeBlockDefinitions: TimeBlockDefinition[];
  onItemClick: (timeBlockDefinition: TimeBlockDefinition) => void;
}

const TimeBlockDefinitionList: Component<ListProps> = (props) => {
  return (
    <GenericList
      items={props.timeBlockDefinitions}
      renderItem={(timeBlockDefinition) => (
        <TimeBlockDefinitionListItem timeBlockDefinition={timeBlockDefinition} />
      )}
      onItemClick={props.onItemClick}
    />
  );
};

export default TimeBlockDefinitionList;

