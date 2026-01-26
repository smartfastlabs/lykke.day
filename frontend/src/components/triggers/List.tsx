import { Component } from "solid-js";
import { Trigger } from "@/types/api";
import SettingsList from "@/components/shared/SettingsList";
import TriggerListItem from "./ListItem";

interface ListProps {
  triggers: Trigger[];
  onItemClick: (trigger: Trigger) => void;
}

const TriggerList: Component<ListProps> = (props) => {
  return (
    <SettingsList
      items={props.triggers}
      getItemLabel={(trigger) => trigger.name}
      renderItem={(trigger) => <TriggerListItem trigger={trigger} />}
      onItemClick={props.onItemClick}
      searchPlaceholder="Search triggers"
      emptyStateLabel="No triggers yet."
    />
  );
};

export default TriggerList;
