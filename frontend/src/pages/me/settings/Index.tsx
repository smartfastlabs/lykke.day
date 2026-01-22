import { Component } from "solid-js";
import {
  faFileLines,
  faRepeat,
  faUser,
  faCalendar,
  faListCheck,
  faCalendarDays,
  faBell,
  faClock,
  faRobot,
  faBrain,
} from "@fortawesome/free-solid-svg-icons";

import LinkGrid, { LinkItem } from "@/components/shared/LinkGrid";

const settingsItems: LinkItem[] = [
  { label: "Day Templates", icon: faFileLines, url: "/me/settings/day-templates" },
  {
    label: "Task Definitions",
    icon: faListCheck,
    url: "/me/settings/task-definitions",
  },
  { label: "Routines", icon: faRepeat, url: "/me/settings/routines" },
  { label: "Time Blocks", icon: faClock, url: "/me/settings/time-blocks" },
  { label: "Notifications", icon: faBell, url: "/me/settings/notifications" },
  { label: "LLM", icon: faBrain, url: "/me/settings/llm" },
  { label: "Profile", icon: faUser, url: "/me/settings/profile" },
  { label: "Calendars", icon: faCalendar, url: "/me/settings/calendars" },
  {
    label: "Recurring Events",
    icon: faCalendarDays,
    url: "/me/settings/recurring-events",
  },
];

const SettingsIndexPage: Component = () => {
  return <LinkGrid items={settingsItems} />;
};

export default SettingsIndexPage;
