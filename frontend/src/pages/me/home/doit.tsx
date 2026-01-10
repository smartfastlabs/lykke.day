import { Component } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import DayView from "@/components/days/View";

export const DoItView: Component = () => {
  const { events, tasks } = useSheppard();

  return <DayView events={events} tasks={tasks} />;
};

export default DoItView;

