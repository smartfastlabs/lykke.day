import Page from "@/components/shared/layout/Page";
import { Component, ParentProps } from "solid-js";

export const SettingsLayout: Component<ParentProps> = (props) => {
  return (
    <Page variant="app" hideFooter>
      <div class="min-h-[100dvh] box-border max-w-5xl mx-2 px-4 md:px-6 lg:px-8 py-8 md:py-10">
        {props.children}
      </div>
    </Page>
  );
};

export default SettingsLayout;

