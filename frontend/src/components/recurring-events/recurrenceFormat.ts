import { CalendarEntrySeries, TaskFrequency } from "@/types/api";

const weekdayNames: Record<string, string> = {
  MO: "Monday",
  TU: "Tuesday",
  WE: "Wednesday",
  TH: "Thursday",
  FR: "Friday",
  SA: "Saturday",
  SU: "Sunday",
};

const digitWeekdayNames: Record<string, string> = {
  "0": "Sunday",
  "1": "Monday",
  "2": "Tuesday",
  "3": "Wednesday",
  "4": "Thursday",
  "5": "Friday",
  "6": "Saturday",
};

const monthNames = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const toOrdinal = (value: number): string => {
  const remainder = value % 100;
  if (remainder >= 11 && remainder <= 13) {
    return `${value}th`;
  }
  switch (value % 10) {
    case 1:
      return `${value}st`;
    case 2:
      return `${value}nd`;
    case 3:
      return `${value}rd`;
    default:
      return `${value}th`;
  }
};

const titleCase = (value: string): string =>
  value
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");

const formatByFrequency = (frequency: TaskFrequency): string => {
  switch (frequency) {
    case "DAILY":
      return "Every day";
    case "WEEKLY":
      return "Every week";
    case "BI_WEEKLY":
      return "Every 2 weeks";
    case "MONTHLY":
      return "Every month";
    case "YEARLY":
      return "Every year";
    case "WORK_DAYS":
      return "Weekdays";
    case "WEEKENDS":
      return "Weekends";
    case "CUSTOM_WEEKLY":
      return "Custom weekly schedule";
    case "ONCE":
      return "One-time event";
    default:
      return titleCase((frequency as string).replaceAll("_", " ").toLowerCase());
  }
};

const parseRRule = (rule: string): string | null => {
  const normalized = rule.startsWith("RRULE:") ? rule.slice(6) : rule;
  // Handle simple comma-separated weekday digits (0-6)
  if (/^[0-6](,[0-6])*$/.test(normalized)) {
    const days = normalized.split(",").map((digit) => digitWeekdayNames[digit]);
    return `Every ${days.join(", ")}`;
  }

  const parts = normalized.split(";").reduce<Record<string, string>>((acc, part) => {
    const [key, value] = part.split("=");
    if (key && value) {
      acc[key.toUpperCase()] = value;
    }
    return acc;
  }, {});

  const freq = parts.FREQ;
  if (!freq) return null;

  if (freq === "DAILY") {
    return "Every day";
  }

  if (freq === "WEEKLY" && parts.BYDAY) {
    const days = parts.BYDAY.split(",").map((code) => weekdayNames[code] ?? code);
    return `Every ${days.join(", ")}`;
  }

  if (freq === "MONTHLY" && parts.BYMONTHDAY) {
    const day = Number(parts.BYMONTHDAY);
    if (!Number.isNaN(day)) {
      return `Every month on the ${toOrdinal(day)}`;
    }
  }

  if (freq === "YEARLY") {
    const day = Number(parts.BYMONTHDAY);
    const month = Number(parts.BYMONTH);
    if (!Number.isNaN(day) && !Number.isNaN(month) && month >= 1 && month <= 12) {
      return `${monthNames[month - 1]} ${toOrdinal(day)}`;
    }
    if (!Number.isNaN(day)) {
      return `Every year on the ${toOrdinal(day)}`;
    }
  }

  return null;
};

export const formatRecurrenceInfo = (series: CalendarEntrySeries): string => {
  if (series.recurrence && series.recurrence.length > 0) {
    for (const rule of series.recurrence) {
      const friendly = parseRRule(rule);
      if (friendly) {
        return friendly;
      }
    }
    // Fallback to raw recurrence if no rule could be parsed
    return series.recurrence.join(", ");
  }

  const startsAt = series.starts_at ? new Date(series.starts_at) : null;
  const hasValidStart = startsAt && !Number.isNaN(startsAt.getTime());

  if (hasValidStart) {
    const weekday = startsAt!.toLocaleDateString(undefined, { weekday: "long" });
    const monthName = monthNames[startsAt!.getMonth()];
    const day = startsAt!.getDate();
    const dayOrdinal = toOrdinal(day);

    switch (series.frequency) {
      case "YEARLY":
        return `${monthName} ${dayOrdinal}`;
      case "MONTHLY":
        return `Every month on the ${dayOrdinal}`;
      case "WEEKLY":
      case "BI_WEEKLY":
      case "CUSTOM_WEEKLY":
        return `Every ${weekday}`;
      case "WORK_DAYS":
        return "Weekdays";
      case "WEEKENDS":
        return "Weekends";
      default:
        break;
    }
  }

  return formatByFrequency(series.frequency);
};

