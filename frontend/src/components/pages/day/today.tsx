import Page from "../../shared/layout/page";
import { Component, createResource } from "solid-js";
import { dayAPI } from "../../../utils/api";

import DayPreview from "../../days/preview";

export const Today: Component = () => {
  const [dayContext] = createResource(dayAPI.getToday);

  return (
    <Page>
      <div class="text-center">
        <h1 class="text-2xl  font-light text-gray-900 mb-1">Today</h1>
        <p class="text-sm text-gray-400">
          {new Date().toLocaleDateString("en-US", {
            weekday: "long",
            month: "long",
            day: "numeric",
          })}
        </p>
      </div>
      <DayPreview dayContext={dayContext()} />
    </Page>
  );
};

export default Today;
