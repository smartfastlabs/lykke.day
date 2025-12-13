import Page from "../shared/layout/page";
import { Component } from "solid-js";
import { useSheppardManager } from "../../providers/sheppard";
import { home } from "solid-heroicons/outline";
import TaskList from "../tasks/list";

export const Home: Component = () => {
  const sheppard = useSheppardManager();
  return (
    <Page>
      <TaskList startTime="05:30" endTime="23:00" tasks={sheppard.tasks} />
    </Page>
  );
};

export default Home;
