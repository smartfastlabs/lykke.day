import { Component } from "solid-js";
import { Icon } from "./Icon";
import { faGear } from "@fortawesome/free-solid-svg-icons";

interface SettingsButtonProps {
  onClick: () => void;
}

const SettingsButton: Component<SettingsButtonProps> = (props) => {
  return (
    <button
      onClick={() => props.onClick()}
      class="fixed bottom-6 right-6 z-50 bg-gray-600 text-white p-4 rounded-full shadow-lg 
             hover:bg-gray-700 active:scale-95 transition-transform duration-150 ease-in-out
             print:hidden"
      aria-label="Settings"
    >
      <Icon icon={faGear} class="w-5 h-5 fill-white" />
    </button>
  );
};

export default SettingsButton;
