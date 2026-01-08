import { Component } from "solid-js";
import {
  faRightToBracket,
  faCalendar,
  faGear,
  faCalendarPlus,
  faBell,
  faHouse,
  faMugHot,
} from "@fortawesome/free-solid-svg-icons";

import Page from "@/components/shared/layout/Page";
import LinkGrid, { LinkItem } from "@/components/shared/linkGrid";
import { alarmAPI } from "@/utils/api";

const navItems: LinkItem[] = [
  { label: "Home", icon: faHouse, url: "/me" },
  { label: "Tomorrow", icon: faCalendarPlus, url: "/me/day/tomorrow" },
  { label: "Notifications", icon: faBell, url: "/me/notifications" },
  { label: "Calendar", icon: faCalendar, url: "/me/nav/calendar" },
  { label: "Settings", icon: faGear, url: "/me/settings" },
  { label: "Login", icon: faRightToBracket, url: "/login" },
  { label: "Alarm", icon: faMugHot, method: alarmAPI.stopAll },
];

const NavPage: Component = () => {
  return (
    <Page>
      <LinkGrid items={navItems} />
    </Page>
  );
};

export default NavPage;
