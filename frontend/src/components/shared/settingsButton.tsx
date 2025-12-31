import { FontAwesomeIcon } from "solid-fontawesome";
import { faGear } from "@fortawesome/free-solid-svg-icons";
import { Component } from "solid-js";

interface SettingsButtonProps {
  onClick: () => void;
}

const SettingsButton: Component<SettingsButtonProps> = (props) => {
  return (
    <button
      onClick={props.onClick}
      class="fixed bottom-6 right-6 z-50 bg-gray-600 text-white p-4 rounded-full shadow-lg 
             hover:bg-gray-700 active:scale-95 transition-transform duration-150 ease-in-out
             print:hidden"
      aria-label="Settings"
    >
      <FontAwesomeIcon icon={faGear as any} />
    </button>
  );
};

export default SettingsButton;
