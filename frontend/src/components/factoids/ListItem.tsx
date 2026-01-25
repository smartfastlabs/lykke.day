import { Component } from "solid-js";
import { Factoid } from "@/types/api";

interface ListItemProps {
  factoid: Factoid;
}

const FactoidListItem: Component<ListItemProps> = (props) => {
  return (
    <div class="flex items-center gap-4">
      <div class="flex-1 min-w-0 space-y-1">
        <span class="text-sm font-semibold text-stone-700 block truncate">
          {props.factoid.content}
        </span>
        <span class="text-xs text-stone-500">
          {props.factoid.factoid_type} • {props.factoid.criticality}
        </span>
      </div>
    </div>
  );
};

export default FactoidListItem;
