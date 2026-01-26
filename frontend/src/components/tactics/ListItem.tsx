import { Component } from "solid-js";
import { Tactic } from "@/types/api";

interface ListItemProps {
  tactic: Tactic;
}

const TacticListItem: Component<ListItemProps> = (props) => {
  return (
    <div class="flex items-center gap-4">
      <div class="flex-1 min-w-0">
        <span class="text-sm font-semibold text-stone-700 block truncate">
          {props.tactic.name}
        </span>
        <span class="text-xs text-stone-500">
          {props.tactic.description || "No description provided"}
        </span>
      </div>
    </div>
  );
};

export default TacticListItem;
