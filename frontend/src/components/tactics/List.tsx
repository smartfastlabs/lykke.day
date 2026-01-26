import { Component } from "solid-js";
import { Tactic } from "@/types/api";
import SettingsList from "@/components/shared/SettingsList";
import TacticListItem from "./ListItem";

interface ListProps {
  tactics: Tactic[];
  onItemClick: (tactic: Tactic) => void;
}

const TacticList: Component<ListProps> = (props) => {
  return (
    <SettingsList
      items={props.tactics}
      getItemLabel={(tactic) => tactic.name}
      renderItem={(tactic) => <TacticListItem tactic={tactic} />}
      onItemClick={props.onItemClick}
      searchPlaceholder="Search tactics"
      emptyStateLabel="No tactics yet."
    />
  );
};

export default TacticList;
