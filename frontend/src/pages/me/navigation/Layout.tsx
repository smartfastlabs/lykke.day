import Page from "@/components/shared/layout/Page";
import { Component, ParentProps } from "solid-js";

interface NavigationLayoutProps extends ParentProps {
  hideFloatingButtons?: boolean;
}

export const NavigationLayout: Component<NavigationLayoutProps> = (props) => {
  return (
    <Page variant="app" hideFooter hideFloatingButtons={props.hideFloatingButtons}>
      <div class="min-h-[100dvh] box-border max-w-4xl mx-auto px-5 md:px-6 lg:px-8 py-8 md:py-10">
        {props.children}
      </div>
    </Page>
  );
};

export default NavigationLayout;
