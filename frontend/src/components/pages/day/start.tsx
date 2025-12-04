import Page from "../../shared/layout/page";
import { getTime } from "../../../utils/dates";
import TimeBadge from "../../shared/timeBadge";
import { createMemo, For, Component, createResource } from "solid-js";
import TaskRow from "../../tasks/row";
import EventRow from "../../events/row";
import { eventAPI, planningAPI } from "../../../utils/api";

export const DayStart: Component = () => {
  const [tasks] = createResource<Any[]>(planningAPI.previewToday);
  const [events] = createResource<Any[]>(eventAPI.getTodays);
  return (
    <Page>
      <For each={tasks()}>{(task) => <TaskRow {...task} />}</For>
      <For each={events()}>{(event) => <EventRow {...event} />}</For>
    </Page>
  );
};

export default DayStart;
