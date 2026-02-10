import { Component } from "solid-js";
import DayBasicsEditor from "@/components/days/DayBasicsEditor";
import { useTomorrowData } from "@/pages/me/tomorrow/useTomorrowData";

export const TomorrowEditPage: Component = () => {
  const { day, refetchAll } = useTomorrowData();

  return (
    <DayBasicsEditor
      day={day}
      label="Tomorrow editor"
      backHref="/me/tomorrow"
      afterSave={refetchAll}
    />
  );
};

export default TomorrowEditPage;

