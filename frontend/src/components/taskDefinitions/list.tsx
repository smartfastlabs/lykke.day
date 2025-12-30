import { Component } from "solid-js";
import { TaskDefinition } from "../../types/api";
import { GenericList } from "../shared/genericList";
import TaskDefinitionListItem from "./listItem";

interface ListProps {
  taskDefinitions: TaskDefinition[];
  onItemClick: (taskDefinition: TaskDefinition) => void;
}

const TaskDefinitionList: Component<ListProps> = (props) => {
  return (
    <GenericList
      items={props.taskDefinitions}
      renderItem={(taskDefinition) => (
        <TaskDefinitionListItem taskDefinition={taskDefinition} />
      )}
      onItemClick={props.onItemClick}
    />
  );
};

export default TaskDefinitionList;

