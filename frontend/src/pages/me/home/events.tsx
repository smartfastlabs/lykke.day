import { Component } from "solid-js";
import { useSheppard } from "@/providers/sheppard";
import DayView from "@/components/days/View";

export const TodaysEventsView: Component = () => {
  const { events } = useSheppard();

  return <DayView tasks={() => []} events={events} />;
};

export default TodaysEventsView;

