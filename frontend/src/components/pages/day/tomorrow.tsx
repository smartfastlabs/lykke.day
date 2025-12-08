import Page from "../../shared/layout/page";
import { Component, Show, createResource } from "solid-js";
import { dayAPI } from "../../../utils/api";

import DayPreview from "../../days/preview";
import { getDateString } from "../../../utils/dates";

export const Tomorrow: Component = () => {
  const [dayContext] = createResource(dayAPI.getTomorrow);

  return (
    <Page>
      <Show when={dayContext()}>
        <div class="text-center">
          <h1 class="text-4xl  font-bold text-gray-500 mb-1">Tomorrow</h1>
          <p class="text-sm text-gray-400">{dayContext()?.day.date}</p>
        </div>
        <DayPreview dayContext={dayContext()} />
      </Show>
    </Page>
  );
};

export default Tomorrow;
