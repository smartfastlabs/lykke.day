import { Component } from "solid-js";
import {
  faFileLines,
  faRepeat,
  faUser,
  faCalendar,
} from "@fortawesome/free-solid-svg-icons";

import Page from "../components/shared/layout/page";
import LinkGrid, { LinkItem } from "../components/shared/linkGrid";

const settingsItems: LinkItem[] = [
  { label: "Day Templates", icon: faFileLines, url: "/settings/day-templates" },
  { label: "Routines", icon: faRepeat, url: "/settings/routines" },
  { label: "Profile", icon: faUser, url: "/settings/profile" },
  { label: "Calendar", icon: faCalendar, url: "/settings/calendar" },
];

const SettingsPage: Component = () => {
  return (
    <Page>
      <LinkGrid items={settingsItems} />
    </Page>
  );
};

export default SettingsPage;

