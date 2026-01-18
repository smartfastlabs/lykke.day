import { NotificationContainer } from "@/providers/notifications";
import BrainDumpButton from "@/components/shared/BrainDumpButton";
import NavButton from "@/components/shared/NavButton";
import Footer from "@/components/shared/layout/Footer";
import { Component, JSX } from "solid-js";

interface PageProps {
  children: JSX.Element;
}

const Page: Component<PageProps> = (props) => {
  return (
    <div class="overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <NotificationContainer />
      <div class="min-h-screen w-full flex flex-col justify-center typography-body">
        <div class="w-full h-full mx-auto md:px-0 max-w-[960px] mt-1 flex-1 flex flex-col">
          {props.children}
        </div>
      </div>
      <Footer />
      <BrainDumpButton />
      <NavButton />
    </div>
  );
};

export default Page;
