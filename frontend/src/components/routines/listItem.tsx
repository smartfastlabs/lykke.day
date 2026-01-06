import { Component } from "solid-js";
import { Routine } from "../../types/api";

interface ListItemProps {
  routine: Routine;
}

const RoutineListItem: Component<ListItemProps> = (props) => {
  return (
    <div class="flex items-center gap-4">
      <div class="flex-1 min-w-0">
        <span class="text-sm text-gray-800 block truncate">{props.routine.name}</span>
        <span class="text-xs text-gray-500">
          {props.routine.category} • {props.routine.routine_schedule.frequency}
          {props.routine.description ? ` • ${props.routine.description}` : ""}
        </span>
      </div>
    </div>
  );
};

export default RoutineListItem;


