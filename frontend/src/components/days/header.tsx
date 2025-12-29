import {
  Component,
  createSignal,
  createMemo,
  For,
  Show,
  Accessor,
} from "solid-js";

import { Icon } from "../shared/icon";
import { formatTimeString } from "../tasks/list";
import { Day } from "../../types/api";

const DayHeader: Component<{ day: Day }> = (props) => {
  const date = () => new Date(props.day.date + "T12:00:00");
  const dayName = () => date().toLocaleDateString("en-US", { weekday: "long" });
  const monthDay = () =>
    date().toLocaleDateString("en-US", { month: "short", day: "numeric" });

  return (
    <header class="px-5 pb-2">
      <div class="flex items-baseline justify-between">
        <div>
          <h1 class="text-2xl font-light tracking-tight text-gray-900">
            {dayName()}
          </h1>
          <p class="text-sm text-gray-400 mt-0.5">{monthDay()}</p>
        </div>
        <Show when={props.day.template_uuid}>
          <span class="text-xs uppercase tracking-wider text-gray-400">
            {props.day.template_uuid}
          </span>
        </Show>
      </div>
    </header>
  );
};

export default DayHeader;
