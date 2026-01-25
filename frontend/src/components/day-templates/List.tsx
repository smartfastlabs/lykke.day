import { Component } from "solid-js";
import { DayTemplate } from "@/types/api";
import SettingsList from "@/components/shared/SettingsList";
import DayTemplateListItem from "./ListItem";

interface ListProps {
  templates: DayTemplate[];
  onItemClick: (template: DayTemplate) => void;
}

const DayTemplateList: Component<ListProps> = (props) => {
  return (
    <SettingsList
      items={props.templates}
      getItemLabel={(template) => template.slug}
      renderItem={(template) => <DayTemplateListItem template={template} />}
      onItemClick={props.onItemClick}
      searchPlaceholder="Search day templates"
      emptyStateLabel="No day templates yet."
    />
  );
};

export default DayTemplateList;
