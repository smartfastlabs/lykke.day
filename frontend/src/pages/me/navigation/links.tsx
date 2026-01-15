import { Component } from "solid-js";
import {
  faRightToBracket,
  faCalendar,
  faGear,
  faHouse,
  faMugHot,
  faTerminal,
} from "@fortawesome/free-solid-svg-icons";

import LinkGrid, { LinkItem } from "@/components/shared/LinkGrid";
import { alarmAPI } from "@/utils/api";

const navItems: LinkItem[] = [
  { label: "Home", icon: faHouse, url: "/me" },
  { label: "Calendar", icon: faCalendar, url: "/me/nav/calendar" },
  { label: "Commands", icon: faTerminal, url: "/me/nav/commands" },
  { label: "Settings", icon: faGear, url: "/me/settings" },
  { label: "Login", icon: faRightToBracket, url: "/login" },
  { label: "Alarm", icon: faMugHot, method: alarmAPI.stopAll },
];

const NavPage: Component = () => {
  return <LinkGrid items={navItems} />;
};

export default NavPage;
