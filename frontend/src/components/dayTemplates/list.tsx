import { Component } from "solid-js";
import { DayTemplate } from "@/types/api";
import { GenericList } from "@/components/shared/genericList";
import DayTemplateListItem from "./listItem";

interface ListProps {
  templates: DayTemplate[];
  onItemClick: (template: DayTemplate) => void;
}

const DayTemplateList: Component<ListProps> = (props) => {
  return (
    <GenericList
      items={props.templates}
      renderItem={(template) => <DayTemplateListItem template={template} />}
      onItemClick={props.onItemClick}
    />
  );
};

export default DayTemplateList;
