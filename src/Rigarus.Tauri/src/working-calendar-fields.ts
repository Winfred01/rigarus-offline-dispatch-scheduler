export type WorkingState = "Working" | "NotWorking" | "Unknown";
export type CalendarScope = "Crew" | "Project";
export type CalendarAssessment = {
  crew_id: number;
  work_item_id: number;
  project_id: number;
  local_date: string;
  slot: "AM" | "PM";
  crew_state: WorkingState;
  work_item_state: WorkingState;
  status: "Matched" | "Blocked" | "Pending";
  reasons: { code: string; scope: string; entity_id: number | null }[];
  crew_revision: number;
  project_revision: number;
  publishable: false;
};
export type CalendarSnapshot = {
  scope: CalendarScope;
  entity_id: number;
  revision: number;
  start_date: string;
  end_date: string;
  entries: { local_date: string; slot: "AM" | "PM"; state: WorkingState }[];
};
export function workingText(state: WorkingState): string {
  return state === "Working"
    ? "Can work"
    : state === "NotWorking"
      ? "Cannot work"
      : "Not recorded";
}
export function calendarMessage(value: CalendarAssessment): string {
  const title =
    value.status === "Matched"
      ? "Calendar matched"
      : value.status === "Blocked"
        ? "Calendar conflict"
        : "Calendar pending";
  return `${title}: Crew ${workingText(value.crew_state)}; Project ${workingText(value.work_item_state)}. All WorkItems inherit Project #${value.project_id}.`;
}
