import { Component } from "solid-js";
import { Routine } from "../../types/api";
import { GenericList } from "../shared/genericList";
import RoutineListItem from "./listItem";

interface ListProps {
  routines: Routine[];
  onItemClick: (routine: Routine) => void;
}

const RoutineList: Component<ListProps> = (props) => {
  return (
    <GenericList
      items={props.routines}
      renderItem={(routine) => <RoutineListItem routine={routine} />}
      onItemClick={props.onItemClick}
    />
  );
};

export default RoutineList;
