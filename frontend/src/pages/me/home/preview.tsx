import { Show, Component } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import DayPreview from "@/components/days/Preview";

export const PreviewView: Component = () => {
  const { dayContext } = useSheppard();

  return (
    <Show when={dayContext()}>
      {(ctx) => <DayPreview dayContext={ctx()} />}
    </Show>
  );
};

export default PreviewView;

