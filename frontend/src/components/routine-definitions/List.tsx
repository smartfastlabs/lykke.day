import { Component } from "solid-js";
import { RoutineDefinition } from "@/types/api";
import SettingsList from "@/components/shared/SettingsList";
import RoutineListItem from "./ListItem";

interface ListProps {
  routineDefinitions: RoutineDefinition[];
  onItemClick: (routineDefinition: RoutineDefinition) => void;
}

const RoutineList: Component<ListProps> = (props) => {
  return (
    <SettingsList
      items={props.routineDefinitions}
      getItemLabel={(routineDefinition) => routineDefinition.name}
      renderItem={(routineDefinition) => (
        <RoutineListItem routineDefinition={routineDefinition} />
      )}
      onItemClick={props.onItemClick}
      searchPlaceholder="Search routine definitions"
      emptyStateLabel="No routine definitions yet."
    />
  );
};

export default RoutineList;
