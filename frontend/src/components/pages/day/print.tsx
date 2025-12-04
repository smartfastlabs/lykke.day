import PrintPage from "../../shared/layout/printPage";
import { For, Component, createResource } from "solid-js";
import TaskRow from "../../tasks/row";
import EventRow from "../../events/row";
import { eventAPI, planningAPI } from "../../../utils/api";

export const DayPrint: Component = () => {
  const [tasks] = createResource<Any[]>(planningAPI.previewToday);
  const [events] = createResource<Any[]>(eventAPI.getTodays);
  return (
    <PrintPage>
      <h1>Ready</h1>
      <For each={tasks()}>{(task) => <TaskRow {...task} />}</For>
      <For each={events()}>{(event) => <EventRow {...event} />}</For>
    </PrintPage>
  );
};

export default DayPrint;
