import { Component } from "solid-js";
import { TimeBlockDefinition } from "@/types/api";

interface ListItemProps {
  timeBlockDefinition: TimeBlockDefinition;
}

const TimeBlockDefinitionListItem: Component<ListItemProps> = (props) => {
  return (
    <div class="flex items-center gap-4">
      <div class="flex-1 min-w-0">
        <span class="text-sm font-semibold text-stone-700 block truncate">
          {props.timeBlockDefinition.name}
        </span>
        <span class="text-xs text-stone-500">
          {props.timeBlockDefinition.type} • {props.timeBlockDefinition.category}
          {props.timeBlockDefinition.description
            ? ` • ${props.timeBlockDefinition.description}`
            : ""}
        </span>
      </div>
    </div>
  );
};

export default TimeBlockDefinitionListItem;

