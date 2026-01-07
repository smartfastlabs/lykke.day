import { useNavigate } from "@solidjs/router";
import { Component, For } from "solid-js";
import Page from "@/components/shared/layout/Page";

interface DayItem {
  label: string;
  date: Date;
  dayOfMonth: number;
  isToday: boolean;
}

function getNextSevenDays(): DayItem[] {
  const days: DayItem[] = [];
  const today = new Date();

  for (let i = 0; i < 20; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);

    days.push({
      label: date.toLocaleDateString("en-US", { weekday: "long" }),
      date,
      dayOfMonth: date.getDate(),
      isToday: i === 0,
    });
  }

  return days;
}

const CalendarPage: Component = () => {
  const navigate = useNavigate();
  const days = getNextSevenDays();

  function onClick(item: DayItem) {
    const dateStr = item.date.toISOString().split("T")[0];
    navigate(`/me/day/${dateStr}`);
  }

  return (
    <Page>
      <div class="grid grid-cols-2 p-5 gap-10 max-w-md mx-auto">
        <For each={days}>
          {(item) => (
            <button
              onClick={() => onClick(item)}
              class={`p-4 aspect-square flex flex-col items-center justify-center gap-2 rounded-lg transition-colors duration-150 ${
                item.isToday
                  ? "bg-gray-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:border-gray-400 hover:text-gray-600"
              }`}
            >
              <span
                class={`text-4xl font-semibold ${item.isToday ? "text-white" : "text-gray-400"}`}
              >
                {item.dayOfMonth}
              </span>
              <span class="text-sm font-medium">{item.label}</span>
            </button>
          )}
        </For>
      </div>
    </Page>
  );
};

export default CalendarPage;
