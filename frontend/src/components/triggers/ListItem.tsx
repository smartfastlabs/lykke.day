import { Component } from "solid-js";
import { Trigger } from "@/types/api";

interface ListItemProps {
  trigger: Trigger;
}

const TriggerListItem: Component<ListItemProps> = (props) => {
  return (
    <div class="flex items-center gap-4">
      <div class="flex-1 min-w-0">
        <span class="text-sm font-semibold text-stone-700 block truncate">
          {props.trigger.name}
        </span>
        <span class="text-xs text-stone-500">
          {props.trigger.description || "No description provided"}
        </span>
      </div>
    </div>
  );
};

export default TriggerListItem;
