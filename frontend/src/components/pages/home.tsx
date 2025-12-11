import Page from "../shared/layout/page";
import { Component } from "solid-js";
import { useTaskManager } from "../../providers/tasks";
import { home } from "solid-heroicons/outline";
import TaskList from "../tasks/list";

export const Home: Component = () => {
  const { tasks } = useTaskManager();
  return (
    <Page>
      HASDFSD
      <TaskList startTime="05:30" endTime="23:00" tasks={tasks} />
    </Page>
  );
};

export default Home;
