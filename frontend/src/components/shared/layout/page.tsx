import { useNavigate } from "@solidjs/router";
import { NotificationContainer } from "../../../providers/notifications";
import NavButton from "../navButton";
import { Component, JSX } from "solid-js";

interface PageProps {
  children: JSX.Element;
}

const Page: Component<PageProps> = (props) => {
  return (
    <div class="overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <NotificationContainer />
      <div class="min-h-screen w-full flex flex-col justify-center typography-body">
        <div class="w-full h-full mx-auto md:px-0 max-w-[960px] mt-4 flex-1 flex flex-col">
          {props.children}
        </div>
      </div>
      <NavButton />
    </div>
  );
};

export default Page;
