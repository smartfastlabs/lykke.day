import { Component, Show } from "solid-js";
import { DayTemplate } from "@/types/api";
import { getIcon } from "@/utils/icons";
import { Icon } from "@/components/shared/icon";

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
          <Icon key={props.template.icon!} />
        </Show>
      </span>

      {/* Template name and task count */}
      <div class="flex-1 min-w-0">
        <span class="text-sm text-gray-800 block truncate">
          {props.template.slug}
        </span>
        <span class="text-xs text-gray-500">
          {props.template.tasks?.length || 0} tasks
        </span>
      </div>
    </div>
  );
};

export default DayTemplateListItem;

