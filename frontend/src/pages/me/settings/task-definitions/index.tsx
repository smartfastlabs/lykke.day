import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import SettingsPage, { ActionButton } from "@/components/shared/settingsPage";
import { taskDefinitionAPI } from "@/utils/api";
import { TaskDefinition } from "@/types/api";
import TaskDefinitionList from "@/components/taskDefinitions/list";

const TaskDefinitionsPage: Component = () => {
  const navigate = useNavigate();
  const [taskDefinitions] = createResource(taskDefinitionAPI.getAll);

  const onClick = (taskDefinition: TaskDefinition) => {
    if (taskDefinition.id) {
      navigate(`/me/settings/task-definitions/${taskDefinition.id}`);
    }
  };

  const actionButtons: ActionButton[] = [
    {
      label: "New Task Definition",
      icon: faPlus,
      onClick: () => navigate("/me/settings/task-definitions/new"),
    },
  ];

  return (
    <SettingsPage heading="Task Definitions" actionButtons={actionButtons}>
      <Show
        when={taskDefinitions()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <TaskDefinitionList
          taskDefinitions={taskDefinitions()!}
          onItemClick={onClick}
        />
      </Show>
    </SettingsPage>
  );
};

export default TaskDefinitionsPage;
