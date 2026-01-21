import { Component } from "solid-js";
import { TaskDefinition } from "@/types/api";

interface ListItemProps {
  taskDefinition: TaskDefinition;
}

const TaskDefinitionListItem: Component<ListItemProps> = (props) => {
  return (
    <div class="flex items-center gap-4">
      {/* Task definition name and type */}
      <div class="flex-1 min-w-0">
        <span class="text-sm text-gray-800 block truncate">
          {props.taskDefinition.name}
        </span>
        <span class="text-xs text-gray-500">
          {props.taskDefinition.type}
          {props.taskDefinition.description
            ? ` • ${props.taskDefinition.description}`
            : ""}
        </span>
      </div>
    </div>
  );
};

export default TaskDefinitionListItem;

