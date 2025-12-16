import Page from "../components/shared/layout/page";
import { Switch, Match, Show, Component, createSignal } from "solid-js";
import { useSheppardManager } from "../providers/sheppard";
import DayView from "../components/days/view";
import DayHeader from "../components/days/header";
import DayPreview from "../components/days/preview";
import DayTabs from "../components/days/tabs";

export const Home: Component = () => {
  const { dayContext, events, tasks, day } = useSheppardManager();
  const [activeTab, setActiveTab] = createSignal("home");
  return (
    <Page>
      <Show when={day()}>
        <DayHeader day={day()} />
        <DayTabs activeTab={activeTab} setActiveTab={setActiveTab} />
        <Switch>
          <Match when={activeTab() == "home"}>
            <DayPreview dayContext={dayContext()} />
          </Match>
          <Match when={activeTab() == "doit"}>
            <DayView day={day} events={events} tasks={tasks} />
          </Match>
          <Match when={activeTab() == "tasks"}>
            <DayView day={day} events={() => []} tasks={tasks} />
          </Match>
          <Match when={activeTab() == "events"}>
            <DayView day={day} tasks={() => []} events={events} />
          </Match>
        </Switch>
      </Show>
    </Page>
  );
};

export default Home;
