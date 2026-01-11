import { Component } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import DayView from "@/components/days/View";

export const TodaysTasksView: Component = () => {
  const { tasks } = useSheppard();

  return <DayView events={() => []} tasks={tasks} />;
};

export default TodaysTasksView;

