import { FontAwesomeIcon } from "solid-fontawesome";
import { faGripVertical } from "@fortawesome/free-solid-svg-icons";
import { useNavigate } from "@solidjs/router";

const NavButton = (props) => {
  const navigate = useNavigate()

  return (
    <button
      onClick={() => navigate("/navigation")}
      class="fixed bottom-6 right-6 z-50 bg-gray-600 text-white w-10 h-10 rounded-full shadow-lg 
             hover:bg-gray-700 active:scale-95 transition-transform duration-150 ease-in-out
             print:hidden"
      aria-label="Settings"
    >
      <FontAwesomeIcon icon={faGripVertical} class="w-6 h-6" />
    </button>
  );
};

export default NavButton;
