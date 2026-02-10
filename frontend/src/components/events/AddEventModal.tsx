import { Component, createEffect, createSignal } from "solid-js";
import { Icon } from "@/components/shared/Icon";
import ModalOverlay from "@/components/shared/ModalOverlay";
import { faCalendarPlus } from "@fortawesome/free-solid-svg-icons";
import type { Event as ApiEvent } from "@/types/api";
import { calendarEntryAPI } from "@/utils/api";

const EVENT_CATEGORIES: Array<NonNullable<ApiEvent["category"]>> = [
  "WORK",
  "PERSONAL",
  "FAMILY",
  "SOCIAL",
  "OTHER",
];

const DURATION_PRESETS = [
  { label: "15 min", minutes: 15 },
  { label: "30 min", minutes: 30 },
  { label: "1 hr", minutes: 60 },
  { label: "1.5 hr", minutes: 90 },
  { label: "2 hr", minutes: 120 },
] as const;

function toDateString(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function todayDateString(): string {
  return toDateString(new Date());
}

function tomorrowDateString(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return toDateString(d);
}

// Week runs Sunday (0) to Saturday (6)
function getThisWeekDates(): Date[] {
  const today = new Date();
  const day = today.getDay();
  const start = new Date(today);
  start.setDate(today.getDate() - day);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    return d;
  });
}

function getNextWeekDates(): Date[] {
  const thisWeek = getThisWeekDates();
  return thisWeek.map((d) => {
    const next = new Date(d);
    next.setDate(d.getDate() + 7);
    return next;
  });
}

function dayLabel(date: Date): string {
  const today = todayDateString();
  const tomorrow = tomorrowDateString();
  const ds = toDateString(date);
  if (ds === today) return "Today";
  if (ds === tomorrow) return "Tomorrow";
  const names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  return names[date.getDay()];
}

type AddEventModalProps = {
  isOpen: boolean;
  onClose: () => void;
  defaultDate: string; // YYYY-MM-DD for default start/end
  onCreated: () => void;
};

type WeekMode = "this" | "next" | null;

function weekModeForDate(dateStr: string): WeekMode {
  const thisWeek = getThisWeekDates().map(toDateString);
  const nextWeek = getNextWeekDates().map(toDateString);
  if (thisWeek.includes(dateStr)) return "this";
  if (nextWeek.includes(dateStr)) return "next";
  return null;
}

export const AddEventModal: Component<AddEventModalProps> = (props) => {
  const [name, setName] = createSignal("");
  const [dateStr, setDateStr] = createSignal(props.defaultDate);
  const [weekMode, setWeekMode] = createSignal<WeekMode>(
    weekModeForDate(props.defaultDate),
  );
  const [startTimeStr, setStartTimeStr] = createSignal("09:00");
  const [durationMinutes, setDurationMinutes] = createSignal(60);
  const [category, setCategory] = createSignal<
    NonNullable<ApiEvent["category"]> | ""
  >("");
  const [isSubmitting, setIsSubmitting] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);

  const thisWeekDates = () =>
    getThisWeekDates().filter(
      (d) => toDateString(d) >= todayDateString(),
    );
  const nextWeekDates = () => getNextWeekDates();

  createEffect(() => {
    if (props.isOpen) {
      setDateStr(props.defaultDate);
      setWeekMode(weekModeForDate(props.defaultDate));
      setStartTimeStr("09:00");
      setDurationMinutes(60);
      setError(null);
    }
  });

  const startsAtISO = (): string => {
    return new Date(`${dateStr()}T${startTimeStr()}`).toISOString();
  };

  const endsAtISO = (): string => {
    const start = new Date(`${dateStr()}T${startTimeStr()}`);
    const end = new Date(start.getTime() + durationMinutes() * 60 * 1000);
    return end.toISOString();
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    const nameVal = name().trim();
    if (!nameVal) {
      setError("Name is required");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await calendarEntryAPI.create({
        name: nameVal,
        starts_at: startsAtISO(),
        ends_at: endsAtISO(),
        category: category() || undefined,
      });
      props.onCreated();
      props.onClose();
      setName("");
      setDateStr(props.defaultDate);
      setWeekMode(weekModeForDate(props.defaultDate));
      setStartTimeStr("09:00");
      setDurationMinutes(60);
      setCategory("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create event");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ModalOverlay
      isOpen={props.isOpen}
      onClose={props.onClose}
      overlayClass="fixed inset-0 z-[60] flex items-center justify-center px-6"
      contentClass="relative w-full max-w-md rounded-2xl border border-white/70 bg-white/95 p-6 shadow-xl backdrop-blur-sm"
    >
      <div class="space-y-4">
        <div class="flex items-center gap-3 text-amber-700">
          <Icon icon={faCalendarPlus} class="w-5 h-5 fill-amber-600" />
          <h2 class="text-lg font-semibold">Add event</h2>
        </div>
        <p class="text-sm text-stone-600">
          Create a Lykke calendar event (timed). It will appear with your other
          calendar entries.
        </p>
        <form onSubmit={handleSubmit} class="space-y-4">
          <div>
            <label for="add-event-name" class="block text-xs font-medium text-stone-500 mb-1">
              Name
            </label>
            <input
              id="add-event-name"
              type="text"
              value={name()}
              onInput={(e) => setName(e.currentTarget.value)}
              class="w-full rounded-lg border border-stone-200 px-3 py-2 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
              placeholder="Event name"
              required
            />
          </div>

          <div>
            <span class="block text-xs font-medium text-stone-500 mb-2">
              Date
            </span>
            <div class="flex w-full items-center gap-2 mb-2">
              <button
                type="button"
                onClick={() => {
                  setWeekMode("this");
                  setDateStr(todayDateString());
                }}
                classList={{
                  "rounded-lg border px-3 py-1.5 text-sm font-medium transition shrink-0": true,
                  "border-amber-400 bg-amber-50 text-amber-700":
                    weekMode() === "this",
                  "border-stone-200 text-stone-600 hover:bg-stone-50":
                    weekMode() !== "this",
                }}
              >
                This week
              </button>
              <button
                type="button"
                onClick={() => {
                  setWeekMode("next");
                  setDateStr(toDateString(getNextWeekDates()[0]));
                }}
                classList={{
                  "rounded-lg border px-3 py-1.5 text-sm font-medium transition shrink-0": true,
                  "border-amber-400 bg-amber-50 text-amber-700":
                    weekMode() === "next",
                  "border-stone-200 text-stone-600 hover:bg-stone-50":
                    weekMode() !== "next",
                }}
              >
                Next week
              </button>
              <input
                type="date"
                value={dateStr()}
                onInput={(e) => {
                  setWeekMode(null);
                  setDateStr(e.currentTarget.value);
                }}
                class="min-w-0 flex-1 rounded-lg border border-stone-200 px-3 py-1.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                aria-label="Pick date"
              />
            </div>
            {weekMode() === "this" && (
              <div class="flex w-full gap-1.5 mt-1.5">
                {thisWeekDates().map((d) => {
                  const ds = toDateString(d);
                  return (
                    <button
                      type="button"
                      onClick={() => setDateStr(ds)}
                      classList={{
                        "flex-1 min-w-0 rounded-lg border px-2.5 py-1 text-xs font-medium transition": true,
                        "border-amber-400 bg-amber-50 text-amber-700":
                          dateStr() === ds,
                        "border-stone-200 text-stone-600 hover:bg-stone-50":
                          dateStr() !== ds,
                      }}
                    >
                      {dayLabel(d)}
                    </button>
                  );
                })}
              </div>
            )}
            {weekMode() === "next" && (
              <div class="flex w-full gap-1.5 mt-1.5">
                {nextWeekDates().map((d) => {
                  const ds = toDateString(d);
                  return (
                    <button
                      type="button"
                      onClick={() => setDateStr(ds)}
                      classList={{
                        "flex-1 min-w-0 rounded-lg border px-2.5 py-1 text-xs font-medium transition": true,
                        "border-amber-400 bg-amber-50 text-amber-700":
                          dateStr() === ds,
                        "border-stone-200 text-stone-600 hover:bg-stone-50":
                          dateStr() !== ds,
                      }}
                    >
                      {dayLabel(d)}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div>
            <label for="add-event-start-time" class="block text-xs font-medium text-stone-500 mb-1">
              Start time
            </label>
            <input
              id="add-event-start-time"
              type="time"
              value={startTimeStr()}
              onInput={(e) => setStartTimeStr(e.currentTarget.value)}
              class="w-full rounded-lg border border-stone-200 px-3 py-2 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
            />
          </div>

          <div>
            <span class="block text-xs font-medium text-stone-500 mb-2">
              Duration
            </span>
            <div class="flex gap-2">
              {DURATION_PRESETS.map((preset) => (
                <button
                  type="button"
                  onClick={() => setDurationMinutes(preset.minutes)}
                  classList={{
                    "flex-1 min-w-0 rounded-lg border px-3 py-1.5 text-sm font-medium transition": true,
                    "border-amber-400 bg-amber-50 text-amber-700":
                      durationMinutes() === preset.minutes,
                    "border-stone-200 text-stone-600 hover:bg-stone-50":
                      durationMinutes() !== preset.minutes,
                  }}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label for="add-event-category" class="block text-xs font-medium text-stone-500 mb-1">
              Category (optional)
            </label>
            <select
              id="add-event-category"
              value={category()}
              onChange={(e) =>
                setCategory(
                  e.currentTarget.value as NonNullable<ApiEvent["category"]> | "",
                )
              }
              class="w-full rounded-lg border border-stone-200 px-3 py-2 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
            >
              <option value="">—</option>
              {EVENT_CATEGORIES.map((c) => (
                <option value={c}>{c.replace("_", " ")}</option>
              ))}
            </select>
          </div>
          {error() && (
            <p class="text-sm text-red-600" role="alert">
              {error()}
            </p>
          )}
          <div class="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => props.onClose()}
              class="flex-1 rounded-lg border border-stone-200 px-4 py-2 text-sm font-medium text-stone-600 transition hover:bg-stone-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting()}
              class="flex-1 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-2 disabled:opacity-50"
            >
              {isSubmitting() ? "Adding…" : "Add event"}
            </button>
          </div>
        </form>
      </div>
    </ModalOverlay>
  );
};

export default AddEventModal;
