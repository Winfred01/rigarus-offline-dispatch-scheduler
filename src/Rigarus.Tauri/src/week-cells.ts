import type { DraftAssignment } from "./assignment-fields";

export type WeekCell = {
  start: number;
  dates: string[];
  assignments: DraftAssignment[];
};

function sameVisit(a: DraftAssignment, b: DraftAssignment): boolean {
  return (
    a.work_item_id === b.work_item_id &&
    a.project_id === b.project_id &&
    a.crew_id === b.crew_id &&
    a.notes === b.notes
  );
}

// A strip is a read-only presentation of saved full-day pairs. Missing shifts,
// parallel jobs and changed notes stay independent; nothing is scheduled here.
export function weekCells(days: string[], rows: DraftAssignment[]): WeekCell[] {
  const byDay = days.map((date) =>
    rows
      .filter((row) => row.local_date === date && row.status === "Draft")
      .sort(
        (a, b) =>
          a.slot.localeCompare(b.slot) || a.crew_id - b.crew_id || a.id - b.id,
      ),
  );
  const pair = (index: number): DraftAssignment | undefined => {
    const day = byDay[index];
    return day?.length === 2 &&
      day[0].slot === "AM" &&
      day[1].slot === "PM" &&
      day[0].id !== day[1].id &&
      sameVisit(day[0], day[1])
      ? day[0]
      : undefined;
  };
  const result: WeekCell[] = [];
  for (let index = 0; index < days.length;) {
    const first = pair(index);
    let end = index + 1;
    if (first) {
      while (end < days.length) {
        const next = pair(end);
        if (!next || !sameVisit(first, next)) break;
        end++;
      }
    }
    result.push({
      start: index,
      dates: days.slice(index, end),
      assignments: byDay.slice(index, end).flat(),
    });
    index = end;
  }
  return result;
}
