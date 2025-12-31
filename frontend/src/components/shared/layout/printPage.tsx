import { Component, JSX } from "solid-js";

interface PrintPageProps {
  children: JSX.Element;
}

const PrintPage: Component<PrintPageProps> = (props) => {
  return (
    <div class="overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <div class="min-h-screen w-full flex flex-col justify-center typography-body">
        <div class="w-full h-full mx-auto md:px-0 max-w-[960px] mt-4 flex-1 flex flex-col">
          {props.children}
        </div>
      </div>
    </div>
  );
};

export default PrintPage;
