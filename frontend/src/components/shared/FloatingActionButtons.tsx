import { Component } from "solid-js";
import BrainDumpButton from "@/components/shared/BrainDumpButton";

type FloatingActionButtonsProps =
  | {
      rightButton?: "nav";
    }
  | {
      rightButton: "settings";
      onSettingsClick: () => void;
    };

const FloatingActionButtons: Component<FloatingActionButtonsProps> = (
  _props
) => {
  return <BrainDumpButton />;
};

export default FloatingActionButtons;
