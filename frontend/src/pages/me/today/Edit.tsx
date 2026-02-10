import { Component } from "solid-js";
import { useStreamingData } from "@/providers/streamingData";
import DayBasicsEditor from "@/components/days/DayBasicsEditor";

export const TodayEditPage: Component = () => {
  const { day, sync } = useStreamingData();
  return (
    <DayBasicsEditor
      day={day}
      label="Today editor"
      backHref="/me/today"
      afterSave={sync}
    />
  );
};

export default TodayEditPage;
