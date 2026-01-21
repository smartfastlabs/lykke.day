import { useNavigate } from "@solidjs/router";
import { Component, For } from "solid-js";

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

  function onClick(_item: DayItem) {
    navigate("/me");
  }

  return (
    <div class="grid grid-cols-2 gap-6 max-w-md mx-auto p-5">
      <For each={days}>
        {(item) => (
          <button
            onClick={() => onClick(item)}
            class={`group p-6 aspect-square flex flex-col items-center justify-center gap-2 rounded-2xl transition-all duration-200 ${
              item.isToday
                ? "bg-gradient-to-br from-amber-500 to-orange-600 text-white shadow-xl shadow-amber-900/20 border border-amber-400/50"
                : "bg-white/70 backdrop-blur-md border border-white/70 text-stone-700 shadow-lg shadow-amber-900/5 hover:bg-white/90 hover:shadow-xl hover:shadow-amber-900/10 hover:border-amber-100/80 hover:scale-105"
            }`}
          >
            <span
              class={`text-4xl font-bold ${
                item.isToday
                  ? "text-white"
                  : "text-amber-500/80 group-hover:text-amber-600"
              }`}
            >
              {item.dayOfMonth}
            </span>
            <span
              class={`text-sm font-semibold ${
                item.isToday
                  ? "text-white/95"
                  : "text-stone-600 group-hover:text-stone-800"
              }`}
            >
              {item.label}
            </span>
          </button>
        )}
      </For>
    </div>
  );
};

export default CalendarPage;
