import Page from "../../components/shared/layout/page";
import { Component, Show, createResource } from "solid-js";
import { useParams } from "@solidjs/router";
import { dayAPI } from "../../utils/api";

import DayPreview from "../../components/days/preview";

export const DayView: Component = () => {
  const params = useParams();
  const [dayContext] = createResource(async () =>
    dayAPI.getContext(params.date)
  );

  return (
    <Page>
      <Show when={dayContext()}>
        <div class="text-center">
          <p class="text-sm text-gray-400">{dayContext()?.day.date}</p>
        </div>
        <DayPreview dayContext={dayContext()} />
      </Show>
    </Page>
  );
};

export default DayView;
