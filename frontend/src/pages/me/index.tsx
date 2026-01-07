import Page from "@/components/shared/layout/Page";
import { Switch, Match, Show, Component, createSignal } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import DayView from "@/components/days/View";
import DayHeader from "@/components/days/Header";
import DayPreview from "@/components/days/Preview";
import DayTabs from "@/components/days/Tabs";

export const Home: Component = () => {
  const { dayContext, events, tasks, day, isLoading } = useSheppard();
  const [activeTab, setActiveTab] = createSignal("home");

  return (
    <Page>
      <Show when={!isLoading() && day()} fallback={<div class="p-8 text-center text-gray-400">Loading...</div>}>
        {(dayValue) => (
          <>
            <DayHeader day={dayValue()} />
            <DayTabs activeTab={activeTab} setActiveTab={setActiveTab} />
            <Switch>
              <Match when={activeTab() === "home"}>
                <Show when={dayContext()}>
                  {(ctx) => <DayPreview dayContext={ctx()} />}
                </Show>
              </Match>
              <Match when={activeTab() === "doit"}>
                <DayView events={events} tasks={tasks} />
              </Match>
              <Match when={activeTab() === "tasks"}>
                <DayView events={() => []} tasks={tasks} />
              </Match>
              <Match when={activeTab() === "events"}>
                <DayView tasks={() => []} events={events} />
              </Match>
            </Switch>
          </>
        )}
      </Show>
    </Page>
  );
};

export default Home;
