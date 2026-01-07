import { useNavigate } from "@solidjs/router";
import { Component } from "solid-js";
import { Icon } from "./Icon";

const NavButton: Component = () => {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate("/me/nav")}
      class="fixed bottom-6 right-6 z-50 bg-gray-600 text-white w-10 h-10 rounded-full shadow-lg 
             hover:bg-gray-700 active:scale-95 transition-transform duration-150 ease-in-out
             print:hidden flex items-center justify-center"
      aria-label="Navigation"
    >
      <Icon key="gripVertical" class="w-5 h-5 fill-white" />
    </button>
  );
};

export default NavButton;
