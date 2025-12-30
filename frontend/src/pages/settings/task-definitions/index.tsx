import { useNavigate } from "@solidjs/router";
import { Component, Show, createResource } from "solid-js";
import Page from "../../../components/shared/layout/page";
import { taskDefinitionAPI } from "../../../utils/api";
import { TaskDefinition } from "../../../types/api";
import TaskDefinitionList from "../../../components/taskDefinitions/list";
import { Icon } from "../../../components/shared/icon";

const TaskDefinitionsPage: Component = () => {
  const navigate = useNavigate();
  const [taskDefinitions] = createResource(taskDefinitionAPI.getAll);

  const onClick = (taskDefinition: TaskDefinition) => {
    if (taskDefinition.id) {
      navigate(`/settings/task-definitions/${taskDefinition.id}`);
    }
  };

  return (
    <Page>
      <Show
        when={taskDefinitions()}
        fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
      >
        <div class="w-full px-5 py-4">
          <div class="flex items-center justify-between mb-6">
            <h1 class="text-2xl font-bold">Task Definitions</h1>
            <button
              onClick={() => navigate("/settings/task-definitions/new")}
              class="flex items-center justify-center w-8 h-8 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="New Task Definition"
            >
              <Icon key="plus" class="w-5 h-5" />
            </button>
          </div>
          <TaskDefinitionList
            taskDefinitions={taskDefinitions()!}
            onItemClick={onClick}
          />
        </div>
      </Show>
    </Page>
  );
};

export default TaskDefinitionsPage;
