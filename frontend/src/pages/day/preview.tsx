import Page from "../../components/shared/layout/page";
import { Component, Show, createResource } from "solid-js";
import { useParams } from "@solidjs/router";
import { dayAPI } from "../../utils/api";

import DayPreview from "../../components/days/preview";

export const DayPreviewPage: Component = () => {
  const params = useParams();
  const [dayContext] = createResource(async () =>
    dayAPI.getContext(params.date)
  );

  return (
    <Page>
      <Show when={dayContext()}>
        {(ctx) => (
          <>
            <div class="text-center">
              <p class="text-sm text-gray-400">{ctx().day.date}</p>
            </div>
            <DayPreview dayContext={ctx()} />
          </>
        )}
      </Show>
    </Page>
  );
};

export default DayPreviewPage;
