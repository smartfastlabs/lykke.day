import { DayOfWeek } from "@/types/api";

export function getDateString(date: Date = new Date()): string {
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, "0"); // Months are 0-indexed
  const day = date.getDate().toString().padStart(2, "0");

  return `${year}-${month}-${day}`;
}

export function getDayOfWeek(date: Date = new Date()): DayOfWeek {
  return date.getDay() as DayOfWeek;
}

export function getTime(date: string, time: string): Date {
  // Expected date format: YYYY-MM-DD (e.g., 2025-02-22)
  // Expected time format: HH:mm (24-hour clock, e.g., 17:45)
  // The resulting Date will be in the user's local timezone.

  const [yearStr, monthStr, dayStr] = date.split("-");
  const [hourStr, minuteStr] = time.split(":");

  const year = parseInt(yearStr, 10);
  const month = parseInt(monthStr, 10) - 1; // JS months are 0-based
  const day = parseInt(dayStr, 10);
  const hour = parseInt(hourStr, 10);
  const minute = parseInt(minuteStr, 10);

  // Construct a Date in the user's local timezone
  const localDate = new Date(year, month, day, hour, minute);
  console.log("Creating date", date, time, localDate);

  return localDate;
}
