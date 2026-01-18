import { useLocation, useNavigate } from "@solidjs/router";
import { Component } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import { faBrain } from "@fortawesome/free-solid-svg-icons";

const BrainDumpButton: Component = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleClick = () => {
    if (
      location.pathname === "/me/brain-dump" ||
      location.pathname === "/me/brain-dump/dump"
    ) {
      navigate("/me");
      return;
    }

    navigate("/me/brain-dump/dump");
  };

  return (
    <button
      onClick={handleClick}
      class="fixed bottom-6 left-6 z-50 bg-gray-600 text-white w-10 h-10 rounded-full shadow-lg 
             hover:bg-gray-700 active:scale-95 transition-transform duration-150 ease-in-out
             print:hidden flex items-center justify-center"
      aria-label="Brain dump"
    >
      <Icon icon={faBrain} class="w-5 h-5 fill-white" />
    </button>
  );
};

export default BrainDumpButton;
