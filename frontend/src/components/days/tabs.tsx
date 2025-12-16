import { Component, For, Signal, Setter } from "solid-js";
import {
  faEye,
  faListCheck,
  faCalendarDay,
  faClock,
  faBowlFood,
  faSmile,
  faHandsWash,
  faMessage,
} from "@fortawesome/free-solid-svg-icons";
import { Icon } from "../shared/icon";

interface TabIndicatorProps {
  activeTab: Signal<string>;
  setActiveTab: Setter<string>;
}

const tabs = [
  { icon: faEye, key: "home" },
  { icon: faClock, key: "doit" },
  { icon: faSmile, key: "lykke" },
  { icon: faMessage, key: "sheppard" },
  { icon: faListCheck, key: "tasks" },
  { icon: faCalendarDay, key: "events" },
  { icon: faBowlFood, key: "food" },
  { icon: faHandsWash, key: "adls" },
];

const DayTabs: Component<TabIndicatorProps> = (props) => {
  return (
    <div class="flex flex-row w-full justify-evenly my-3">
      <For each={tabs}>
        {(tab) => (
          <button
            type="button"
            onClick={() => props.setActiveTab(tab.key)}
            class="flex flex-col items-center gap-1"
          >
            <Icon
              icon={tab.icon}
              class={`w-6 h-6 ${props.activeTab() === tab.key ? "fill-gray-900" : "fill-gray-300"}`}
            />
          </button>
        )}
      </For>
    </div>
  );
};

export default DayTabs;
