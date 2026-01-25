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
      class="fixed bottom-6 right-6 z-50 flex h-10 w-10 items-center justify-center rounded-full bg-gray-600 text-white shadow-lg
             transition-transform duration-150 ease-in-out hover:bg-gray-700 active:scale-95
             print:hidden"
      aria-label="Settings"
    >
      <Icon icon={faGear} class="h-5 w-5 fill-white" />
    </button>
  );
};

export default SettingsButton;
