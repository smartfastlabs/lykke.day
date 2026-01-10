import Page from "@/components/shared/layout/Page";
import { Show, Component, createMemo, ParentProps } from "solid-js";
import { useLocation } from "@solidjs/router";
import { useSheppard } from "@/providers/sheppard";
import DayHeader from "@/components/days/Header";
import DayTabs from "@/components/days/Tabs";

export const HomeLayout: Component<ParentProps> = (props) => {
  const { day, isLoading } = useSheppard();
  const location = useLocation();

  const activeTab = createMemo(() => {
    const path = location.pathname;
    if (path === "/me/today" || path === "/me/today/") return "home";
    if (path === "/me/today/doit") return "doit";
    if (path === "/me/today/tasks") return "tasks";
    if (path === "/me/today/events") return "events";
    if (path === "/me/today/sheppard") return "sheppard";
    return "home";
  });

  return (
    <Page>
      <Show
        when={!isLoading() && day()}
        fallback={<div class="p-8 text-center text-gray-400">Loading...</div>}
      >
        {(dayValue) => (
          <>
            <DayHeader day={dayValue()} />
            <DayTabs activeTab={activeTab()} />
            {props.children}
          </>
        )}
      </Show>
    </Page>
  );
};

export default HomeLayout;
