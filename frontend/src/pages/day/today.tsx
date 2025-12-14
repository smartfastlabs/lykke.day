import Page from "../../components/shared/layout/page";
import { Component, createResource } from "solid-js";

import { useSheppardManager } from "../../providers/sheppard";

import DayPreview from "../../components/days/preview";

export const Today: Component = () => {
  const { dayContext } = useSheppardManager();

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
