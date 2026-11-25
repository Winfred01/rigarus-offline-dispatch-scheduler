import type { DraftAssignment } from "./assignment-fields";
import { validLocalDate } from "./assignment-fields";
import { weekDays } from "./week";
import { calendarMessage } from "./working-calendar-fields";

export function locateProblem(id: number, row?: DraftAssignment): string {
  if (!Number.isSafeInteger(id) || id <= 0 || !row || row.id !== id)
    return "This saved visit could not be found. Reload assignments and try again.";
  if (row.status !== "Draft")
    return `Draft #${id} is ${String(row.status).toLowerCase()} and cannot be located on the active board.`;
  if (!validLocalDate(row.local_date))
    return "This visit has an invalid local date. Reload assignments for review.";
  return "";
}

export function locateWeek(date: string): string {
  const first = weekDays(date)[0];
  // At the storage boundary the displayed Sunday may be in year zero.
  return validLocalDate(first) ? first : date;
}

export function revealFilters(
  filters: { crew: string; project: string },
  row: Pick<DraftAssignment, "crew_id" | "project_id">,
) {
  return {
    crew:
      !filters.crew || Number(filters.crew) === row.crew_id ? filters.crew : "",
    project:
      !filters.project || Number(filters.project) === row.project_id
        ? filters.project
        : "",
  };
}

// Observations already returned for this saved visit, not a full safety scan.
export function reviewFeedback(row: DraftAssignment): string[] {
  const reasons: string[] = [];
  if (!row.calendar_assessment)
    reasons.push("Calendar assessment not loaded. Reload assignments.");
  else if (row.calendar_assessment.status !== "Matched")
    reasons.push(calendarMessage(row.calendar_assessment));
  if (!row.staffing?.configured) reasons.push("Actual staffing not assigned.");
  else if (!row.staffing.workers.length)
    reasons.push("Actual staffing is explicitly empty.");
  if (!row.crew_active) reasons.push("Crew is inactive.");
  return reasons;
}

export function locateScroll(
  viewport: { top: number; left: number; width: number; height: number },
  card: { top: number; left: number; width: number; height: number },
  scroll: { top: number; left: number; height: number; width: number },
  sticky: { top: number; left: number },
) {
  const height = Math.max(1, viewport.height - sticky.top);
  const width = Math.max(1, viewport.width - sticky.left);
  const clamp = (value: number, maximum: number) =>
    Math.max(0, Math.min(value, Math.max(0, maximum)));
  return {
    top: clamp(
      scroll.top +
        card.top -
        viewport.top -
        sticky.top -
        (card.height <= height ? (height - card.height) / 2 : 0),
      scroll.height - viewport.height,
    ),
    left: clamp(
      scroll.left +
        card.left -
        viewport.left -
        sticky.left -
        (card.width <= width ? (width - card.width) / 2 : 0),
      scroll.width - viewport.width,
    ),
  };
}

export function createLocateCue<T = number>(
  publish: (id: T | undefined) => void,
  clock: {
    schedule: (run: () => void, ms: number) => number;
    cancel: (id: number) => void;
  },
) {
  let timer: number | undefined;
  let epoch = 0;
  function dispose() {
    epoch++;
    if (timer !== undefined) clock.cancel(timer);
    timer = undefined;
  }
  return {
    dispose,
    clear() {
      dispose();
      publish(undefined);
    },
    start(id: T) {
      dispose();
      const current = epoch;
      publish(id);
      timer = clock.schedule(() => {
        if (current !== epoch) return;
        timer = undefined;
        publish(undefined);
      }, 2000);
    },
  };
}
