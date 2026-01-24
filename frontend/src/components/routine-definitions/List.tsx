import { Component } from "solid-js";
import { RoutineDefinition } from "@/types/api";
import { GenericList } from "@/components/shared/GenericList";
import RoutineListItem from "./ListItem";

interface ListProps {
  routineDefinitions: RoutineDefinition[];
  onItemClick: (routineDefinition: RoutineDefinition) => void;
}

const RoutineList: Component<ListProps> = (props) => {
  return (
    <GenericList
      items={props.routineDefinitions}
      renderItem={(routineDefinition) => (
        <RoutineListItem routineDefinition={routineDefinition} />
      )}
      onItemClick={props.onItemClick}
    />
  );
};

export default RoutineList;
