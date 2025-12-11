import { useNavigate } from "@solidjs/router";
import { Component, For } from "solid-js";
import { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import {
  faRightToBracket,
  faGear,
  faCalendarDay,
  faCalendarPlus,
  faBell,
  faHouse,
} from "@fortawesome/free-solid-svg-icons";

import Page from "../shared/layout/page";

interface NavItem {
  label: string;
  icon: IconDefinition;
  url: string;
}

const navItems: NavItem[] = [
  { label: "Home", icon: faHouse, url: "/" },
  { label: "Login", icon: faRightToBracket, url: "/login" },
  { label: "Settings", icon: faGear, url: "/settings" },
  { label: "Today", icon: faCalendarDay, url: "/today" },
  { label: "Tomorrow", icon: faCalendarPlus, url: "/tomorrow" },
  { label: "Notifications", icon: faBell, url: "/notifications" },
];

const NavPage: Component = () => {
  const navigate = useNavigate();

  return (
    <Page>
      <div class="grid grid-cols-2 gap-10 max-w-md mx-auto">
        <For each={navItems}>
          {(item) => (
            <button
              onClick={() => navigate(item.url)}
              class="aspect-square flex flex-col items-center justify-center gap-2 bg-gray-100 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-600 transition-colors duration-150"
            >
              <svg
                viewBox={`0 0 ${item.icon.icon[0]} ${item.icon.icon[1]}`}
                class="w-18 h-18 fill-gray-400"
              >
                <path d={item.icon.icon[4] as string} />
              </svg>
              <span class="text-sm font-medium">{item.label}</span>
            </button>
          )}
        </For>
      </div>
    </Page>
  );
};

export default NavPage;
