import { Component, For } from "solid-js";
import { DayTemplate } from "../../types/api";
import DayTemplateListItem from "./listItem";

interface ListProps {
  templates: DayTemplate[];
  onItemClick: (template: DayTemplate) => void;
}

const DayTemplateList: Component<ListProps> = (props) => {
  return (
    <div class="space-y-2">
      <For each={props.templates}>
        {(template) => (
          <DayTemplateListItem
            template={template}
            onClick={props.onItemClick}
          />
        )}
      </For>
    </div>
  );
};

export default DayTemplateList;

