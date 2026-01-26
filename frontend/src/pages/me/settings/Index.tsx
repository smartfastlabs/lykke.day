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
  faBrain,
  faLightbulb,
  faBolt,
  faBullseye,
} from "@fortawesome/free-solid-svg-icons";

import LinkGrid, { LinkItem } from "@/components/shared/LinkGrid";

const settingsItems: LinkItem[] = [
  { label: "Day Templates", icon: faFileLines, url: "/me/settings/day-templates" },
  {
    label: "Task Definitions",
    icon: faListCheck,
    url: "/me/settings/task-definitions",
  },
  {
    label: "Routine Definitions",
    icon: faRepeat,
    url: "/me/settings/routine-definitions",
  },
  { label: "Triggers", icon: faBolt, url: "/me/settings/triggers" },
  { label: "Tactics", icon: faBullseye, url: "/me/settings/tactics" },
  { label: "Factoids", icon: faLightbulb, url: "/me/settings/factoids" },
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
