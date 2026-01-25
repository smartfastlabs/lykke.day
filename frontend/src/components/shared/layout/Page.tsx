import { NotificationContainer } from "@/providers/notifications";
import Footer from "@/components/shared/layout/Footer";
import FloatingActionButtons from "@/components/shared/FloatingActionButtons";
import { Component, JSX, Show } from "solid-js";

interface PageProps {
  children: JSX.Element;
  hideFooter?: boolean;
  hideFloatingButtons?: boolean;
  variant?: "default" | "app";
}

const Page: Component<PageProps> = (props) => {
  const isApp = () => props.variant === "app";

  return (
    <div class="overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <NotificationContainer />
      <div
        class={`w-full flex flex-col typography-body ${
          isApp() ? "min-h-[100dvh] justify-start" : "min-h-screen justify-center"
        }`}
      >
        <div
          class={`w-full h-full mx-auto md:px-0 flex-1 flex flex-col ${
            isApp() ? "max-w-none mt-0" : "max-w-[960px] mt-1"
          }`}
        >
          {props.children}
        </div>
      </div>
      <Show when={!props.hideFooter}>
        <Footer />
      </Show>
      <Show when={!props.hideFloatingButtons}>
        <FloatingActionButtons />
      </Show>
    </div>
  );
};

export default Page;
