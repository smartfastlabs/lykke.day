import { Component, Show } from "solid-js";
import { DayTemplate } from "@/types/api";
import { getIcon } from "@/utils/icons";
import { Icon } from "@/components/shared/Icon";

interface ListItemProps {
  template: DayTemplate;
}

const DayTemplateListItem: Component<ListItemProps> = (props) => {
  const icon = () => props.template.icon ? getIcon(props.template.icon) : null;

  return (
    <div class="flex items-center gap-4">
      {/* Icon column */}
      <span class="w-4 flex-shrink-0 flex items-center justify-center">
        <Show when={icon()}>
          <Icon key={props.template.icon!} class="w-4 h-4 fill-amber-500/80" />
        </Show>
      </span>

      {/* Template name and routine definition count */}
      <div class="flex-1 min-w-0">
        <span class="text-sm font-semibold text-stone-700 block truncate">
          {props.template.slug}
        </span>
        <span class="text-xs text-stone-500">
          {props.template.routine_definition_ids?.length || 0} routine
          definition
          {props.template.routine_definition_ids?.length === 1 ? "" : "s"}
        </span>
      </div>
    </div>
  );
};

export default DayTemplateListItem;

