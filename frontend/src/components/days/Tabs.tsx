import { Component, For } from "solid-js";
import { useNavigate } from "@solidjs/router";
import {
  faEye,
  faListCheck,
  faCalendarDay,
  faClock,
  faMessage,
} from "@fortawesome/free-solid-svg-icons";
import { Icon } from "@/components/shared/Icon";

interface TabIndicatorProps {
  activeTab: string;
}

const tabs = [
  { icon: faEye, key: "home" },
  { icon: faClock, key: "doit" },
  { icon: faMessage, key: "sheppard" },
  { icon: faListCheck, key: "tasks" },
  { icon: faCalendarDay, key: "events" },
];

const DayTabs: Component<TabIndicatorProps> = (props) => {
  const navigate = useNavigate();

  const getTabUrl = (key: string) => {
    if (key === "home") return "/me/today";
    return `/me/today/${key}`;
  };

  return (
    <div class="flex flex-row w-full justify-evenly my-3">
      <For each={tabs}>
        {(tab) => (
          <button
            type="button"
            onClick={() => navigate(getTabUrl(tab.key))}
            class="flex flex-col items-center gap-1"
          >
            <Icon
              icon={tab.icon}
              class={`w-6 h-6 ${props.activeTab === tab.key ? "fill-gray-900" : "fill-gray-300"}`}
            />
          </button>
        )}
      </For>
    </div>
  );
};

export default DayTabs;
