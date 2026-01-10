import Page from "@/components/shared/layout/Page";
import { Component, ParentProps } from "solid-js";

export const SettingsLayout: Component<ParentProps> = (props) => {
  return <Page>{props.children}</Page>;
};

export default SettingsLayout;

