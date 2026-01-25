import { Component } from "solid-js";
import { Factoid } from "@/types/api";
import SettingsList from "@/components/shared/SettingsList";
import FactoidListItem from "./ListItem";

interface ListProps {
  factoids: Factoid[];
  onItemClick: (factoid: Factoid) => void;
}

const FactoidList: Component<ListProps> = (props) => {
  return (
    <SettingsList
      items={props.factoids}
      getItemLabel={(factoid) => factoid.content}
      renderItem={(factoid) => <FactoidListItem factoid={factoid} />}
      onItemClick={props.onItemClick}
      searchPlaceholder="Search factoids"
      emptyStateLabel="No factoids yet."
    />
  );
};

export default FactoidList;
