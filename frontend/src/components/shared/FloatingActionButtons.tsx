import { Component } from "solid-js";
import { useNavigate } from "@solidjs/router";
import BrainDumpButton from "@/components/shared/BrainDumpButton";
import SettingsButton from "@/components/shared/SettingsButton";

const FloatingActionButtons: Component = () => {
  const navigate = useNavigate();

  return (
    <>
      <BrainDumpButton />
      <SettingsButton onClick={() => navigate("/me/nav")} />
    </>
  );
};

export default FloatingActionButtons;
