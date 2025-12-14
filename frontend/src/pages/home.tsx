import Page from "../components/shared/layout/page";
import { Show, Component } from "solid-js";
import { useSheppardManager } from "../providers/sheppard";
import { home } from "solid-heroicons/outline";
import TaskList from "../components/tasks/list";
import DayView from "../components/days/view";

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
