import { FontAwesomeIcon } from "solid-fontawesome";
import { faGripVertical } from "@fortawesome/free-solid-svg-icons";
import { useNavigate } from "@solidjs/router";
import { Component } from "solid-js";

const NavButton: Component = () => {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate("/nav")}
      class="fixed bottom-6 right-6 z-50 bg-gray-600 text-white w-10 h-10 rounded-full shadow-lg 
             hover:bg-gray-700 active:scale-95 transition-transform duration-150 ease-in-out
             print:hidden"
      aria-label="Settings"
    >
      <FontAwesomeIcon icon={faGripVertical as any} />
    </button>
  );
};

export default NavButton;
