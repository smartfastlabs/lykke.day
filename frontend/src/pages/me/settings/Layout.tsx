import Page from "@/components/shared/layout/Page";
import { Component, ParentProps } from "solid-js";

export const SettingsLayout: Component<ParentProps> = (props) => {
  return (
    <Page>
      <div class="max-w-4xl mx-auto px-5 md:px-6 lg:px-8 py-8 md:py-10">
        {props.children}
      </div>
    </Page>
  );
};

export default SettingsLayout;

