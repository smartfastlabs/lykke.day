import { Component } from "solid-js";
import { TaskDefinition } from "@/types/api";
import SettingsList from "@/components/shared/SettingsList";
import TaskDefinitionListItem from "./ListItem";

interface ListProps {
  taskDefinitions: TaskDefinition[];
  onItemClick: (taskDefinition: TaskDefinition) => void;
}

const TaskDefinitionList: Component<ListProps> = (props) => {
  return (
    <SettingsList
      items={props.taskDefinitions}
      getItemLabel={(taskDefinition) => taskDefinition.name}
      renderItem={(taskDefinition) => (
        <TaskDefinitionListItem taskDefinition={taskDefinition} />
      )}
      onItemClick={props.onItemClick}
      searchPlaceholder="Search task definitions"
      emptyStateLabel="No task definitions yet."
    />
  );
};

export default TaskDefinitionList;

