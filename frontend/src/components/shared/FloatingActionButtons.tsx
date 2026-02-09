import { Component, Show, createMemo } from "solid-js";
import { useLocation } from "@solidjs/router";
import BrainDumpButton from "@/components/shared/BrainDumpButton";
import MeMenuButton from "@/components/shared/MeMenuButton";

const FloatingActionButtons: Component = () => {
  const location = useLocation();

  const isMeRoute = createMemo(() => location.pathname.startsWith("/me"));

  return (
    <Show when={isMeRoute()}>
      <BrainDumpButton />
      <MeMenuButton />
    </Show>
  );
};

export default FloatingActionButtons;
