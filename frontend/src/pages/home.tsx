import Page from "../components/shared/layout/page";
import { Show, Component } from "solid-js";
import { useSheppardManager } from "../providers/sheppard";
import DayView from "../components/days/view";
import DayPreview from "../components/days/preview";

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
