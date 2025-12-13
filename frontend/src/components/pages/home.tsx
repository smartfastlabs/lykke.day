import Page from "../shared/layout/page";
import { Show, Component } from "solid-js";
import { useSheppardManager } from "../../providers/sheppard";
import { home } from "solid-heroicons/outline";
import TaskList from "../tasks/list";
import DayView from "./day/view";

export const Home: Component = () => {
  const { events, tasks, day } = useSheppardManager();
  return (
    <Page>
      <Show when={day()}>
        <DayView day={day} events={events} tasks={tasks} />
      </Show>
    </Page>
  );
};

export default Home;
