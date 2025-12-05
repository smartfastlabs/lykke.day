import Page from "../../shared/layout/page";
import { getTime } from "../../../utils/dates";
import TimeBadge from "../../shared/timeBadge";
import { createMemo, For, Component, createResource } from "solid-js";
import TaskRow from "../../tasks/row";
import EventRow from "../../events/row";
import { eventAPI, planningAPI } from "../../../utils/api";

export const DayStart: Component = () => {
  const [dayContext] = createResource(planningAPI.previewToday);

  const dailyTasks = createMemo(() => {
    return dayContext()?.tasks || [];
  });

  const specialTasks = createMemo(() => {
    return dailyTasks().filter((task) => task.task_definition.is_special);
  });

  const dailyEvents = createMemo(() => {
    return dayContext()?.events || [];
  });

  return (
    <Page>
      <For each={dayContext()?.tasks}>{(task) => <TaskRow {...task} />}</For>
      <For each={dayContext()?.events}>
        {(event) => <EventRow {...event} />}
      </For>
    </Page>
  );
};

export default DayStart;
