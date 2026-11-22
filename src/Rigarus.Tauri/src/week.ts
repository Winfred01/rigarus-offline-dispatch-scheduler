// Calendar arithmetic uses UTC only as an integer day counter, never as a work-date conversion.
export function dayNumber(value: string): number {
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(0);
  date.setUTCFullYear(year, month - 1, day);
  date.setUTCHours(0, 0, 0, 0);
  return date.getTime() / 86400000;
}

export function shiftDay(value: string, offset: number): string {
  return new Date((dayNumber(value) + offset) * 86400000)
    .toISOString()
    .split("T")[0];
}

export function weekDays(value: string): string[] {
  const weekday = new Date(dayNumber(value) * 86400000).getUTCDay();
  return Array.from({ length: 7 }, (_, index) =>
    shiftDay(value, index - weekday),
  );
}

export function inWeek(date: string, days: string[]): boolean {
  return days.includes(date);
}

export function displayDate(value: string): string {
  return new Date(dayNumber(value) * 86400000).toLocaleDateString("en-CA", {
    timeZone: "UTC",
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
