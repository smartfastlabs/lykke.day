import { Component } from "solid-js";
import {
  faFileLines,
  faRepeat,
  faUser,
  faCalendar,
  faListCheck,
} from "@fortawesome/free-solid-svg-icons";

import Page from "@/components/shared/layout/page";
import LinkGrid, { LinkItem } from "@/components/shared/linkGrid";

const settingsItems: LinkItem[] = [
  { label: "Day Templates", icon: faFileLines, url: "/me/settings/day-templates" },
  {
    label: "Task Definitions",
    icon: faListCheck,
    url: "/me/settings/task-definitions",
  },
  { label: "Routines", icon: faRepeat, url: "/me/settings/routines" },
  { label: "Profile", icon: faUser, url: "/me/settings/profile" },
  { label: "Calendar", icon: faCalendar, url: "/me/settings/calendar" },
];

const SettingsPage: Component = () => {
  return (
    <Page>
      <LinkGrid items={settingsItems} />
    </Page>
  );
};

export default SettingsPage;
