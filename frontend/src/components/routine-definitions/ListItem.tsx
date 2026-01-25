import { Component } from "solid-js";
import { RoutineDefinition } from "@/types/api";

interface ListItemProps {
  routineDefinition: RoutineDefinition;
}

const RoutineListItem: Component<ListItemProps> = (props) => {
  return (
    <div class="flex items-center gap-4">
      <div class="flex-1 min-w-0">
        <span class="text-sm font-semibold text-stone-700 block truncate">
          {props.routineDefinition.name}
        </span>
        <span class="text-xs text-stone-500">
          {props.routineDefinition.category} •{" "}
          {props.routineDefinition.routine_definition_schedule.frequency}
          {props.routineDefinition.description
            ? ` • ${props.routineDefinition.description}`
            : ""}
        </span>
      </div>
    </div>
  );
};

export default RoutineListItem;
