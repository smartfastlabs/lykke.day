import { Component } from "solid-js";
import { DayTemplate } from "../../types/api";
import { getIcon } from "../../utils/icons";

interface ListItemProps {
  template: DayTemplate;
  onClick: (template: DayTemplate) => void;
}

const DayTemplateListItem: Component<ListItemProps> = (props) => {
  const icon = props.template.icon ? getIcon(props.template.icon) : null;

  return (
    <button
      onClick={() => props.onClick(props.template)}
      class="w-full flex items-center gap-4 p-4 bg-gray-100 rounded-lg text-left hover:bg-gray-200 transition-colors duration-150"
    >
      {icon && (
        <svg
          viewBox={`0 0 ${icon.icon[0]} ${icon.icon[1]}`}
          class="w-8 h-8 flex-shrink-0 fill-gray-600"
        >
          <path d={icon.icon[4] as string} />
        </svg>
      )}
      <div class="flex-1">
        <div class="font-medium text-gray-900">{props.template.slug}</div>
        <div class="text-sm text-gray-500">
          {props.template.tasks?.length || 0} tasks
        </div>
      </div>
    </button>
  );
};

export default DayTemplateListItem;

