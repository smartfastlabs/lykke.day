import { Component } from "solid-js";
import BrainDumpButton from "@/components/shared/BrainDumpButton";
import NavButton from "@/components/shared/NavButton";
import SettingsButton from "@/components/shared/SettingsButton";

type FloatingActionButtonsProps =
  | {
      rightButton?: "nav";
    }
  | {
      rightButton: "settings";
      onSettingsClick: () => void;
    };

const FloatingActionButtons: Component<FloatingActionButtonsProps> = (
  props
) => {
  return (
    <>
      <BrainDumpButton />
      {props.rightButton === "settings" ? (
        <SettingsButton onClick={props.onSettingsClick} />
      ) : (
        <NavButton />
      )}
    </>
  );
};

export default FloatingActionButtons;
